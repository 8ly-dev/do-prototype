"""
This module contains the route handlers for the Do application.

It defines the functions that handle HTTP requests to various routes,
such as the homepage, login, logout, and project views.
"""

from starlette.responses import HTMLResponse, RedirectResponse
from starlette.requests import Request
from starlette.exceptions import HTTPException
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from do.auth import verify_access_token, generate_access_token
from do.db_models import get_db

# Use the same template environment as app.py
templates = Environment(
    loader=FileSystemLoader(Path(__file__).parent.parent / "resources" / "templates")
)


async def homepage(request: Request):
    """
    Handle requests to the homepage.

    If the user is authenticated, render the dashboard with their projects and top task.
    Otherwise, render the login page.

    Args:
        request: The incoming HTTP request

    Returns:
        An HTML response with either the dashboard or login page
    """
    token = request.cookies.get("SESSION_TOKEN")
    if token:
        user_id = verify_access_token(token)
        if user_id:
            db = get_db()
            user = db.get_user_by_id(user_id)
            if user:
                projects = db.get_projects_by_user(user_id)
                top_task = db.get_users_top_task(user_id)

                template = templates.get_template("dashboard.html")
                return HTMLResponse(template.render(projects=projects, top_task=top_task))

            else:
                response = RedirectResponse(url="/", status_code=302)
                response.delete_cookie("SESSION_TOKEN")
                return response

    template = templates.get_template("login.html")
    return HTMLResponse(template.render())


async def login_get(request: Request):
    """
    Handle GET requests to the login page.

    Simply redirects to the homepage, which will show the login page if needed.

    Args:
        request: The incoming HTTP request

    Returns:
        A redirect response to the homepage
    """
    # Simply redirect to the home page
    return RedirectResponse(url="/", status_code=302)


async def login_post(request: Request):
    """
    Handle POST requests to the login endpoint.

    Process the login form submission. If a username is provided, either find the existing
    user or create a new one, then set a session token cookie and redirect to the homepage.
    If no username is provided, redirect back to the login page.

    Args:
        request: The incoming HTTP request with form data

    Returns:
        A redirect response to the homepage with a session token cookie if login is successful,
        or a redirect back to the login page if no username is provided
    """
    form_data = await request.form()
    username = form_data.get("username")

    if username:
        db = get_db()
        user = db.get_user_by_username(username)

        if user:
            # User exists, use their ID
            user_id = user.id
        else:
            # User doesn't exist, create a new user
            user_id = db.insert_user(username)

        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie("SESSION_TOKEN", generate_access_token(user_id))
        return response

    # If no username provided, redirect back to login page
    return RedirectResponse(url="/", status_code=302)


async def logout(request: Request):
    """
    Handle requests to the logout endpoint.

    Delete the session token cookie and redirect to the homepage.

    Args:
        request: The incoming HTTP request

    Returns:
        A redirect response to the homepage with the session token cookie deleted
    """
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("SESSION_TOKEN")
    return response


async def project_view(request: Request):
    """
    Handle requests to view a specific project.

    If the user is authenticated, render the project page with the project details,
    tasks, and other projects. If the user is not authenticated or the project is
    not found, redirect to the homepage or raise a 404 error.

    Args:
        request: The incoming HTTP request with the project slug in path_params

    Returns:
        An HTML response with the project page

    Raises:
        HTTPException: If the project is not found
    """
    token = request.cookies.get("SESSION_TOKEN")
    if not token:
        return RedirectResponse(url="/", status_code=302)

    user_id = verify_access_token(token)
    if not user_id:
        return RedirectResponse(url="/", status_code=302)

    # Get project slug from URL
    project_slug = request.path_params["project_slug"]

    # Get all projects for the user
    db = get_db()
    projects = db.get_projects_by_user(user_id)

    # Find the project that matches the slug
    current_project = None
    for project in projects:
        # Create a slug from the project name
        slug = project.name.lower().replace(" ", "-")
        if slug == project_slug:
            current_project = project
            break

    if not current_project:
        raise HTTPException(status_code=404, detail="Project Not Found.")

    # Get tasks for this project
    tasks = db.get_tasks_by_project(current_project.id)

    # Get top task for the user (same as dashboard)
    top_task = db.get_users_top_task(user_id)

    template = templates.get_template("project.html")
    return HTMLResponse(template.render(
        projects=projects,
        current_project=current_project,
        tasks=tasks,
        top_task=top_task
    ))


async def learn_more(request: Request):
    """
    Handle requests to the Learn More page.

    This function renders the learn_more.html template.

    Args:
        request: The incoming HTTP request

    Returns:
        An HTML response with the Learn More page
    """
    template = templates.get_template("learn_more.html")
    return HTMLResponse(template.render())
