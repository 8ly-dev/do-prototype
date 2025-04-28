"""
This module contains the WebSocket handler for the Flowstate chat feature.
"""

import asyncio
import json
import logging
import random
import time

from starlette.websockets import WebSocket

from flowstate.agents import FlowstateAgent
from flowstate.auth import verify_access_token
from flowstate.db_models import get_db

logger = logging.getLogger(__name__)


async def flowstate_chat_websocket(websocket: WebSocket):
    """
    Handle WebSocket connections for the Flowstate chat feature.

    This function authenticates the user, sets up a FlowstateAgent, and processes messages
    from the client. It also handles task completion requests and sends responses back
    to the client.

    Args:
        websocket: The WebSocket connection

    Returns:
        None
    """
    db = get_db()
    logger.info("Flowstate chat WebSocket connecting")
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
    agent = FlowstateAgent(user_id=user_id, project=project)

    if not project:
        projects = db.get_projects_by_user(user_id)
        if len(projects) == 0:
            start = time.time()
            # Show typing indicator
            await websocket.send_json({
                "kind": "command",
                "command": "typing"
            })
            
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

            # Send welcome message in structured format
            await websocket.send_json({
                "kind": "reply",
                "reply": welcome_message
            })


    async def nudge_user():
        nonlocal nudge_delay, nudge_task
        await asyncio.sleep(nudge_delay)
        
        # Show typing indicator
        await websocket.send_json({
            "kind": "command",
            "command": "typing"
        })
        
        nudge_message = await agent.send_prompt(
            f"This is the software developer: {user.username} is inactive and hasn't done anything yet. Send a message "
            f"to inspire them to get started. Remember to use the example formatter."
        )
        
        # Send nudge message in structured format
        await websocket.send_json({
            "kind": "reply",
            "reply": nudge_message
        })

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

            # Parse the message
            try:
                json_data = json.loads(data)
                
                # Check if this is a task completion request
                if isinstance(json_data, dict) and json_data.get('type') == 'complete_task':
                    task_id = json_data.get('task_id')
                    if task_id:
                        # Delete the task
                        db.delete_task(int(task_id))
                        continue
                
                # Check if this is a prompt message
                if isinstance(json_data, dict) and json_data.get('kind') == 'prompt':
                    # Extract the prompt text
                    prompt = json_data.get('prompt', '')
                    
                    # Show typing indicator
                    await websocket.send_json({
                        "kind": "command",
                        "command": "typing"
                    })
                    
                    # Process the message
                    response = await agent.send_prompt(prompt)
                    
                    # Send the response in the structured format
                    await websocket.send_json({
                        "kind": "reply",
                        "reply": response
                    })
                    continue
            except (json.decoder.JSONDecodeError, TypeError):
                # Legacy format - plain text message
                # Show typing indicator
                await websocket.send_json({
                    "kind": "command",
                    "command": "typing"
                })
                
                # Process the message
                response = await agent.send_prompt(data)
                
                # Send the response in the structured format
                await websocket.send_json({
                    "kind": "reply",
                    "reply": response
                })
    except Exception as e:
        logger.exception("Error in Flowstate chat websocket: %s", str(e))
        closed = True
    finally:
        if not nudge_task.done():
            nudge_task.cancel()
        if not closed:
            await websocket.close()
