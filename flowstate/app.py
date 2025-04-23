"""
This module contains the main web application for Flowstate.

It defines the routes, request handlers, and WebSocket handlers for the application.
The application uses Starlette as the web framework and Jinja2 for templating.
"""

import asyncio
import json
import random
import re
import time

import pydantic_ai
import starlette
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.routing import Route, WebSocketRoute
from starlette.requests import Request
from starlette.websockets import WebSocket
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from flowstate.agents import LearnMoreAgent, LearnMoreSuggestedActionsAgent, TaskAgent
from flowstate.auth import verify_access_token, generate_access_token
from flowstate.db_models import get_db
from flowstate.task_views import task_view, task_update

templates = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates")
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
            projects = db.get_projects_by_user(user_id)
            top_task = db.get_users_top_task(user_id)

            template = templates.get_template("dashboard.html")
            return HTMLResponse(template.render(projects=projects, top_task=top_task))

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


async def chat_websocket(websocket: WebSocket):
    """
    Handle WebSocket connections for the chat feature.

    This function authenticates the user, sets up a TaskAgent, and processes messages
    from the client. It also handles task completion requests and sends responses back
    to the client.

    Args:
        websocket: The WebSocket connection

    Returns:
        None
    """
    db = get_db()
    print("CONNECTING")
    session_token = websocket.cookies.get("SESSION_TOKEN")
    user_id = verify_access_token(session_token) if session_token else None
    project_id = websocket.path_params.get("project_id")

    if not user_id:
        await websocket.close(code=401)
        return

    await websocket.accept()
    closed = False

    user = db.get_user_by_id(user_id)
    project = db.get_project(project_id) if project_id else None
    agent = TaskAgent(user_id=user_id, project=project)

    if not project:
        projects = db.get_projects_by_user(user_id)
        if len(projects) == 0:
            start = time.time()
            await websocket.send_text("!!COMMAND: typing!!")
            welcome_message = await agent.send_prompt(
                f"This is the software developer: {user.username} is new a new user, please great them and let them "
                f"know how they can get started, mention a feature or two. Use markdown to send a large welcome "
                f"heading followed by two sentence using normal formatting (say the user's name somewhere in there). "
                f"Make sure to mention that you use 'natural language'. Use emoji. Don't forget that you are a helpful "
                f"assistant that is an innate extension of the user. Be sure to remain invisible, only refer to the "
                f"app Flowstate, not yourself. Remember to use the example formatter."
            )
            duration = time.time() - start
            if duration < 1.5:
                await asyncio.sleep(1.5 - duration)

            await websocket.send_text(welcome_message)


    async def nudge_user():
        nonlocal nudge_delay, nudge_task
        await asyncio.sleep(nudge_delay)
        nudge_message = await agent.send_prompt(
            f"This is the software developer: {user.username} is inactive and hasn't done anything yet. Send a message "
            f"to inspire them to get started. Remember to use the example formatter."
        )
        await websocket.send_text(nudge_message)

        nudge_delay = random.randint(60, 300)
        nudge_task = loop.create_task(nudge_user())

    loop = asyncio.get_running_loop()
    nudge_delay = 5 * 60
    nudge_task = loop.create_task(nudge_user())

    try:
        while True:
            data = await websocket.receive_text()
            if not nudge_task.done():
                nudge_task.cancel()

            # Check if this is a task completion request
            try:
                json_data = json.loads(data)
            except (json.decoder.JSONDecodeError, TypeError):
                pass
            else:
                if isinstance(json_data, dict) and json_data.get('type') == 'complete_task':
                    task_id = json_data.get('task_id')
                    if task_id:
                        # Delete the task
                        db.delete_task(int(task_id))
                        continue

            # Normal message processing
            response = await agent.send_prompt(data)
            print(response)
            await websocket.send_text(response)
    except starlette.websockets.WebSocketDisconnect:
        closed = True
    finally:
        if not closed:
            await websocket.close()


async def learn_more_chat_websocket(websocket: WebSocket):
    """
    Handle WebSocket connections for the learn more page.

    This function sets up a LearnMoreAgent, sends the README content to the client,
    and processes messages from the client. It also handles suggested actions and
    tool usage messages.

    Args:
        websocket: The WebSocket connection

    Returns:
        None
    """
    print("CONNECTING")
    await websocket.accept()
    closed = False
    db = get_db()
    session_token = websocket.cookies.get("SESSION_TOKEN")
    user_id = verify_access_token(session_token) if session_token else None
    user = db.get_user_by_id(user_id) if user_id else None

    agent = LearnMoreAgent(user, websocket)
    await websocket.send_json(
        {
            "type": "command",
            "command": "typing",
        }
    )
    await asyncio.sleep(1)
    await websocket.send_json(
        {
            "type": "reply",
            "reply": agent.readme,
        }
    )
    await websocket.send_json(
        {
            "type": "actions",
            "actions": (await LearnMoreSuggestedActionsAgent(context=agent.readme).send_prompt()).to_list(),
        }
    )
    try:
        while not closed:
            try:
                data = await websocket.receive_text()
                try:
                    response = await agent.send_prompt(data)
                except pydantic_ai.exceptions.ModelHTTPError:
                    await websocket.send_json(
                        {
                            "type": "reply",
                            "reply": "I'm sorry, something went wrong. Please try again in a moment.",
                        }
                    )
                    await websocket.send_json(
                        {
                            "type": "command",
                            "command": "reload",
                        }
                    )
                    raise
                else:
                    response = clean_response(response)
                    await websocket.send_json(
                        {
                            "type": "reply",
                            "reply": response,
                        }
                    )
                    actions_agent = LearnMoreSuggestedActionsAgent(agent.history[:5])
                    suggested_actions = await actions_agent.send_prompt(response)
                    if suggested_actions:
                        await websocket.send_json(
                            {
                                "type": "actions",
                                "actions": suggested_actions.to_list(),
                            }
                        )

            except pydantic_ai.exceptions.ModelHTTPError as e:
                await websocket.send_json(
                    {
                        "type": "using",
                        "tool_message": f"Oops, something went wrong. Please try again in a moment.",
                    }
                )
                print(e)

            except starlette.websockets.WebSocketDisconnect:
                closed = True

    finally:
        if not closed:
            await websocket.close()


async def http_exception(request: Request, exc: HTTPException):
    """
    Handle HTTP exceptions with custom templates.

    This function renders a custom 404 page for 404 errors and a generic error page
    for other HTTP exceptions.

    Args:
        request: The incoming HTTP request
        exc: The HTTP exception that was raised

    Returns:
        An HTML response with the appropriate error page and status code
    """
    if exc.status_code == 404:
        template = templates.get_template("404.html")
        return HTMLResponse(template.render(), status_code=404)

    # For other HTTP exceptions, return the default response
    return HTMLResponse(f"<h1>{exc.status_code} Error</h1><p>{exc.detail}</p>", status_code=exc.status_code)


async def not_found(request: Request, exc: Exception):
    """
    Handle 404 errors when a route is not found.

    This function renders a custom 404 page when a route is not found.

    Args:
        request: The incoming HTTP request
        exc: The exception that was raised

    Returns:
        An HTML response with the 404 page and a 404 status code
    """
    template = templates.get_template("404.html")
    return HTMLResponse(template.render(), status_code=404)


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


app = Starlette(
    debug=True,
    routes=[
        Route("/", homepage),
        Route("/learn-more", learn_more),
        Route("/login", login_get, methods=["GET"]),
        Route("/login", login_post, methods=["POST"]),
        Route("/logout", logout),
        Route("/project/{project_slug}", project_view),
        Route("/task/{task_id:int}", task_view),
        Route("/task/{task_id:int}/update", task_update, methods=["POST"]),
        WebSocketRoute("/ws", chat_websocket),
        WebSocketRoute("/ws/{project_id:int}", chat_websocket),
        WebSocketRoute("/ws/learn-more", learn_more_chat_websocket),
    ],
    exception_handlers={
        404: not_found,
        HTTPException: http_exception,
    }
)


def clean_response(response: str) -> str:
    """
    Clean the response text by ensuring there's a space before "8ly".

    This function adds a space before "8ly" if there isn't already a space before it,
    to ensure proper formatting in the response text.

    Args:
        response: The response text to clean

    Returns:
        The cleaned response text
    """
    return re.sub(r'([^\s])(8ly)', r'\g<1> \g<2>', response)
