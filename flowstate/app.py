from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.routing import Route, WebSocketRoute
from starlette.requests import Request
from starlette.websockets import WebSocket, WebSocketState
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from flowstate.agents import TaskAgent
from flowstate.auth import verify_access_token, verify_login_token, generate_access_token, send_auth_email
from flowstate.db_models import get_db

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
    token = request.query_params.get("t")
    if token:
        email = verify_login_token(token)
        if email:
            db = get_db()
            user = db.get_user_by_email(email)

            if user:
                # User exists, use their ID
                user_id = user.id
            else:
                # User doesn't exist, create a new user
                user_id = db.insert_user(email)

            response = RedirectResponse(url="/", status_code=302)
            response.set_cookie("SESSION_TOKEN", generate_access_token(user_id))
            return response

    return RedirectResponse(url="/", status_code=302)


async def login_post(request: Request):
    form_data = await request.form()
    email = form_data.get("email")

    if email:
        send_auth_email(email)
        template = templates.get_template("email_sent.html")
        return HTMLResponse(template.render(email=email))

    # If no email provided, redirect back to login page
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
    session_token = websocket.cookies.get("SESSION_TOKEN")
    user_id = verify_access_token(session_token) if session_token else None

    if not user_id:
        await websocket.close(code=4001)
        return

    await websocket.accept()
    agent = TaskAgent(user_id=user_id)
    db = get_db()
    try:
        while True:
            data = await websocket.receive_text()

            # Check if this is a task completion request
            try:
                json_data = eval(data)
                if isinstance(json_data, dict) and json_data.get('type') == 'complete_task':
                    task_id = json_data.get('task_id')
                    if task_id:
                        # Delete the task
                        db.delete_task(int(task_id))
                        await websocket.send_text(f"Task completed successfully.")
                        continue
            except:
                # Not JSON or not a task completion request, treat as normal message
                pass

            # Normal message processing
            await websocket.send_text(
                await agent.send_prompt(data)
            )
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if websocket.state != WebSocketState.DISCONNECTED:
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
        WebSocketRoute("/ws", chat_websocket),
    ],
    exception_handlers={
        404: not_found,
        HTTPException: http_exception,
    }
)
