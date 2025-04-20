import starlette
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.routing import Route, WebSocketRoute
from starlette.requests import Request
from starlette.websockets import WebSocket, WebSocketState
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import json

from flowstate.agents import TaskAgent
from flowstate.auth import verify_access_token, generate_access_token
from flowstate.db_models import get_db
from flowstate.task_views import task_view, task_update

templates = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates")
)


async def homepage(request: Request):
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
    # Simply redirect to the home page
    return RedirectResponse(url="/", status_code=302)


async def login_post(request: Request):
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
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("SESSION_TOKEN")
    return response


async def project_view(request: Request):
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

    project = db.get_project(project_id)
    agent = TaskAgent(user_id=user_id, project=project)
    try:
        while True:
            data = await websocket.receive_text()

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


async def http_exception(request: Request, exc: HTTPException):
    """
    Handle HTTP exceptions with custom templates.
    """
    if exc.status_code == 404:
        template = templates.get_template("404.html")
        return HTMLResponse(template.render(), status_code=404)

    # For other HTTP exceptions, return the default response
    return HTMLResponse(f"<h1>{exc.status_code} Error</h1><p>{exc.detail}</p>", status_code=exc.status_code)


async def not_found(request: Request, exc: Exception):
    """
    Handle 404 errors when a route is not found.
    """
    template = templates.get_template("404.html")
    return HTMLResponse(template.render(), status_code=404)


app = Starlette(
    debug=True,
    routes=[
        Route("/", homepage),
        Route("/login", login_get, methods=["GET"]),
        Route("/login", login_post, methods=["POST"]),
        Route("/logout", logout),
        Route("/project/{project_slug}", project_view),
        Route("/task/{task_id:int}", task_view),
        Route("/task/{task_id:int}/update", task_update, methods=["POST"]),
        WebSocketRoute("/ws", chat_websocket),
        WebSocketRoute("/ws/{project_id:int}", chat_websocket),
    ],
    exception_handlers={
        404: not_found,
        HTTPException: http_exception,
    }
)
