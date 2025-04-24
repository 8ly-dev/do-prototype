"""
This module contains the WebSocket handler for the learn more page.
"""

import asyncio

import pydantic_ai
import starlette
from starlette.websockets import WebSocket

from flowstate.agents import LearnMoreAgent, LearnMoreSuggestedActionsAgent
from flowstate.auth import verify_access_token
from flowstate.db_models import get_db
from flowstate.chats.utils import clean_response


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