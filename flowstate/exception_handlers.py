"""
This module contains the exception handlers for the Flowstate application.

It defines the functions that handle HTTP exceptions and 404 errors.
"""

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

# Use the same template environment as app.py
templates = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates")
)


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