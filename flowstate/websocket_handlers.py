"""
This module contains the WebSocket handlers for the Flowstate application.

It defines the functions that handle WebSocket connections for chat functionality
and the learn more page.
"""

import asyncio
import json
import random
import re
import time

import pydantic_ai
import starlette
from starlette.websockets import WebSocket

from flowstate.agents import LearnMoreAgent, LearnMoreSuggestedActionsAgent, TaskAgent
from flowstate.auth import verify_access_token
from flowstate.db_models import get_db


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
    suggestion_agent = LearnMoreSuggestedActionsAgent()
    await websocket.send_json(
        {
            "type": "command",
            "command": "typing",
        }
    )
    name = f" {user.username}" if user else ""
    await websocket.send_json(
        {
            "type": "using",
            "tool_message": f"Hi{name}, I'm thinking, one moment please",
        }
    )
    actions, _ = await asyncio.gather(
        suggestion_agent.send_prompt(f"AGENT:\n{agent.readme}"),
        asyncio.sleep(2),
    )
    await websocket.send_json(
        {
            "type": "reply",
            "reply": agent.readme,
        }
    )
    await websocket.send_json(
        {
            "type": "actions",
            "actions": actions.to_list(),
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
                    suggested_actions = await suggestion_agent.send_prompt(
                        f"USER:\n{data}\n"
                        f"AGENT:\n{response}\n"
                    )
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
    return re.sub(r'([^\s\-_"\'./\\])(8ly)', r'\g<1> \g<2>', response)