from starlette.applications import Starlette
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.routing import Route
from starlette.requests import Request
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

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


app = Starlette(
    debug=True,
    routes=[
        Route("/", homepage),
        Route("/login", login_get, methods=["GET"]),
        Route("/login", login_post, methods=["POST"]),
        Route("/logout", logout),
    ]
)
