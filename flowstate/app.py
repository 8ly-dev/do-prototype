"""
This module contains the main web application for Flowstate.

It serves as the entry point for the application, configuring the Starlette app
with routes, WebSocket handlers, exception handlers, and static files.
"""

from pathlib import Path

from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.routing import Route, WebSocketRoute, Mount
from starlette.staticfiles import StaticFiles

from flowstate.views import homepage, login_get, login_post, logout, project_view, learn_more
from flowstate.chats import flowstate_chat_websocket, LearnMoreChat
from flowstate.chats.login import LoginChat
from flowstate.exception_handlers import http_exception, not_found
from flowstate.task_views import task_view, task_update


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
        WebSocketRoute("/ws", flowstate_chat_websocket),
        WebSocketRoute("/ws/{project_id:int}", flowstate_chat_websocket),
        WebSocketRoute("/ws/learn-more", LearnMoreChat.create_chat),
        WebSocketRoute("/ws/login", LoginChat.create_chat),
        Mount("/static", app=StaticFiles(directory=Path(__file__).parent.parent / "resources" / "static"), name="static"),
    ],
    exception_handlers={
        404: not_found,
        HTTPException: http_exception,
    }
)
