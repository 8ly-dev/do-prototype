"""
Task view handlers for the Flowstate application.

This module provides request handlers for viewing and updating tasks,
with support for different task types (todo, email, reminder, calendar, create_task).
"""

from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.exceptions import HTTPException
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import json

from flowstate.agents import EmailAgent, EmailHelperSuggestions
from flowstate.auth import verify_access_token
from flowstate.db_models import get_db, Task
from flowstate.emails import Email, Sender

# Use the same template environment as app.py
templates = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates")
)

# Add custom filters
def fromjson_filter(value):
    """
    Convert a JSON string to a Python object.

    This filter is used in templates to parse JSON data stored in task descriptions.

    Args:
        value: The JSON string to convert

    Returns:
        The Python object represented by the JSON string
    """
    return json.loads(value)

templates.filters['fromjson'] = fromjson_filter

async def task_view(request: Request):
    """
    Handle requests to view a task.

    This function renders different templates based on the task type (todo, email, reminder, 
    calendar, create_task). For email tasks, it also generates email suggestions using 
    the EmailAgent.

    Args:
        request: The incoming HTTP request with the task_id in path_params

    Returns:
        An HTML response with the appropriate task template

    Raises:
        HTTPException: If the task is not found or the user doesn't have access to it
    """
    # Check authentication
    token = request.cookies.get("SESSION_TOKEN")
    if not token:
        return RedirectResponse(url="/", status_code=302)

    user_id = verify_access_token(token)
    if not user_id:
        return RedirectResponse(url="/", status_code=302)

    # Get task ID from URL
    task_id = request.path_params["task_id"]

    # Get the task
    db = get_db()
    task = db.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task Not Found.")

    # Check if the user has access to this task
    project = db.get_project(task.project_id)
    if not project or project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access Denied.")

    # Get all projects for the user (for sidebar)
    projects = db.get_projects_by_user(user_id)

    # Get top task for the user (same as dashboard)
    top_task = db.get_users_top_task(user_id)

    # Get user information
    user = db.get_user_by_id(user_id)

    # Render the appropriate template based on task type
    values = {}
    if task.task_type == "todo":
        template = templates.get_template("task_todo.html")
    elif task.task_type == "email":
        email_agent = EmailAgent[None, EmailHelperSuggestions](user)
        email_suggestions = await email_agent.send_prompt(
            f"I need you to write an email for the {project.name} project. Here are some more "
            f"specific instructions:\n{task.title}\n{task.description}",
        )

        template = templates.get_template("task_email.html")
        values = {
            "subject": email_suggestions.subject,
            "message": email_suggestions.message,
        }
    elif task.task_type == "reminder":
        template = templates.get_template("task_reminder.html")
    elif task.task_type == "calendar":
        template = templates.get_template("task_calendar.html")
    elif task.task_type == "create_task":
        template = templates.get_template("task_create.html")
    else:
        # Default to todo task view if type is unknown
        template = templates.get_template("task_todo.html")

    return HTMLResponse(template.render(
        projects=projects,
        current_project=project,
        task=task,
        top_task=top_task,
        user=user,
        **values,
    ))

async def task_update(request: Request):
    """
    Handle requests to update a task.

    This function processes form submissions for different task types and updates
    the task in the database accordingly. For email tasks, it can also send the email
    if requested.

    Args:
        request: The incoming HTTP request with the task_id in path_params and form data

    Returns:
        A redirect response to the task view page or project page

    Raises:
        HTTPException: If the task is not found or the user doesn't have access to it
    """
    # Check authentication
    token = request.cookies.get("SESSION_TOKEN")
    if not token:
        return RedirectResponse(url="/", status_code=302)

    user_id = verify_access_token(token)
    if not user_id:
        return RedirectResponse(url="/", status_code=302)

    # Get task ID from URL
    task_id = request.path_params["task_id"]

    # Get the task
    db = get_db()
    task = db.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task Not Found.")

    # Check if the user has access to this task
    project = db.get_project(task.project_id)
    if not project or project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access Denied.")

    # Get user information
    user = db.get_user_by_id(user_id)

    # Process form data based on task type
    form_data = await request.form()

    updates = {}

    if task.task_type == "todo":
        # todo task updates
        if "title" in form_data:
            updates["title"] = form_data["title"]
        if "description" in form_data:
            updates["description"] = form_data["description"]
        if "due_date" in form_data:
            updates["due_date"] = form_data["due_date"]
        if "priority" in form_data:
            updates["priority"] = int(form_data["priority"])

    elif task.task_type == "email":
        # Email task updates
        if "title" in form_data:
            updates["title"] = form_data["title"]
        if "to" in form_data:
            # Store email details in the description as JSON
            email_data = json.loads(task.description or "{}")
            email_data["to"] = form_data["to"]
            if "cc" in form_data:
                email_data["cc"] = form_data["cc"]
            if "bcc" in form_data:
                email_data["bcc"] = form_data["bcc"]
            if "message" in form_data:
                email_data["message"] = form_data["message"]
            updates["description"] = json.dumps(email_data)

    elif task.task_type == "reminder":
        # Reminder task updates
        if "title" in form_data:
            updates["title"] = form_data["title"]
        if "message" in form_data or "date" in form_data or "time" in form_data:
            reminder_data = json.loads(task.description or "{}")
            if "message" in form_data:
                reminder_data["message"] = form_data["message"]
            if "date" in form_data:
                reminder_data["date"] = form_data["date"]
            if "time" in form_data:
                reminder_data["time"] = form_data["time"]
            updates["description"] = json.dumps(reminder_data)

    elif task.task_type == "calendar":
        # Calendar task updates
        if "title" in form_data:
            updates["title"] = form_data["title"]
        if "message" in form_data or "date" in form_data or "time" in form_data:
            calendar_data = json.loads(task.description or "{}")
            if "message" in form_data:
                calendar_data["message"] = form_data["message"]
            if "date" in form_data:
                calendar_data["date"] = form_data["date"]
            if "time" in form_data:
                calendar_data["time"] = form_data["time"]
            updates["description"] = json.dumps(calendar_data)

    elif task.task_type == "create_task":
        # Create task updates (yes/no choice)
        if "choice" in form_data:
            updates["description"] = form_data["choice"]

    # Update the task if there are any changes
    if updates:
        db.update_task(task_id, **updates)

    # Redirect back to the project page
    project_slug = project.name.lower().replace(" ", "-")
    return RedirectResponse(url=f"/project/{project_slug}", status_code=302)
