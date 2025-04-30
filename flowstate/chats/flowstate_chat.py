"""
This module contains the WebSocket handler for the Flowstate chat feature.
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from typing import Literal, TypedDict

from starlette.websockets import WebSocket, WebSocketState

from flowstate.agents import FlowstateAgent
from flowstate.auth import verify_access_token
from flowstate.chats.base_chat import BaseChat
from flowstate.db_models import get_db

logger = logging.getLogger(__name__)


class PromptData(TypedDict):
    kind: Literal["prompt"]
    prompt: str


class CompleteTaskData(TypedDict):
    type: Literal["complete_task"]
    task_id: str


@dataclass
class CommandModel:
    command: str
    kind: Literal["command"] = "command"


@dataclass
class ReplyModel:
    reply: str
    kind: Literal["reply"] = "reply"


@dataclass
class UsingModel:
    tool_message: str
    kind: Literal["using"] = "using"


class FlowstateChat(BaseChat):
    """
    Handle WebSocket connections for the Flowstate chat feature.

    This class authenticates the user, sets up a FlowstateAgent, and processes messages
    from the client. It also handles task completion requests and sends responses back
    to the client.
    """

    def __init__(self, websocket: WebSocket):
        super().__init__(websocket)
        self.db = get_db()
        self.logger = logging.getLogger(__name__)
        self.session_token = websocket.cookies.get("SESSION_TOKEN")
        self.user_id = verify_access_token(self.session_token) if self.session_token else None
        self.project_id = websocket.path_params.get("project_id")
        self.user = None
        self.project = None
        self.agent = None
        self.nudge_task = None

    async def on_connect(self):
        """Handle the initial connection setup."""
        if not self.user_id:
            await self.websocket.close(code=401)
            return

        self.user = self.db.get_user_by_id(self.user_id)
        self.project = self.db.get_project(self.project_id) if self.project_id else None

        # Initialize the agent with the chat instance
        self.agent = FlowstateAgent(user_id=self.user_id, project=self.project, chat=self)

        if not self.project:
            projects = self.db.get_projects_by_user(self.user_id)
            if len(projects) == 0:
                await self.send_welcome_message()
            else:
                await self.send_next_task()

        # Start the nudge task
        self.nudge_task = self.loop.create_task(self.nudge_user())

    async def send_next_task(self):
        """Send the next task to the user."""
        start = time.time()
        await self.send_json(CommandModel(command="typing"))

        message = await self.agent.send_prompt(
            f"Brief the user on what they need to do next, keep it short (two sentences) and don't get into the details. "
            f"Your response must have a markdown title. Do not intro your response. Follow up with a "
            f"horizontal line and ask the user what they need to do.\n\nExpected "
            f"response format:\n\n## 🙂 Task Title\nTask brief\n---\nCall to action"
        )

        # Add a small delay for a more natural feel
        duration = time.time() - start
        if duration < 1.5:
            await asyncio.sleep(1.5 - duration)

        # Send welcome message
        await self.send_json(ReplyModel(reply=message))

    async def send_welcome_message(self):
        """Send a welcome message to new users."""
        start = time.time()

        # Show typing indicator
        await self.send_json(CommandModel(command="typing"))

        welcome_message = await self.agent.send_prompt(
            f"{self.user.username} is a new user, let them know how they can get started, mention a feature or two. "
            f"Use markdown to send a large welcome heading followed by two sentence using normal formatting. Make sure "
            f"to mention that Flowstate understands 'natural language'. Use emoji. Don't forget that you are a helpful "
            f"assistant that is an innate extension of the user. Be sure to remain invisible, only refer to the app "
            f"Flowstate, not yourself."
        )

        # Add a small delay for a more natural feel
        duration = time.time() - start
        if duration < 1.5:
            await asyncio.sleep(1.5 - duration)

        # Send welcome message
        await self.send_json(ReplyModel(reply=welcome_message))

    async def nudge_user(self):
        """Send a nudge message to inactive users."""
        try:
            await asyncio.sleep(random.randint(60, 300))

            # Show typing indicator
            await self.send_json(CommandModel(command="typing"))

            nudge_message = await self.agent.send_prompt(
                f"The user is inactive and hasn't done anything yet. Send a message to inspire them to get started."
            )

            # Send nudge message
            await self.send_json(ReplyModel(reply=nudge_message))

            self.nudge_task = self.loop.create_task(self.nudge_user())
        except asyncio.CancelledError:
            # Task was cancelled, which is expected when user interacts
            pass

    async def send_using(self, tool_message: str):
        """Send a tool usage message to the client."""
        print(f"USING: {tool_message}")
        await self.send_json(UsingModel(tool_message=tool_message))

    async def prompt_handler(self, data: PromptData):
        """Handle prompt messages from the client."""
        # Cancel any pending nudge
        if self.nudge_task and not self.nudge_task.done():
            self.nudge_task.cancel()

        # Show typing indicator
        await self.send_json(CommandModel(command="typing"))

        # Process the message
        print("Sending prompt:", data["prompt"])
        response = await self.agent.send_prompt(data["prompt"])
        print("Got response:", response)

        # Send the response
        await self.send_json(ReplyModel(reply=response))

        # Schedule next nudge
        self.nudge_task = self.loop.create_task(self.nudge_user())

    async def complete_task_handler(self, data: CompleteTaskData):
        """Handle task completion requests."""
        task_id = data.get('task_id')
        if task_id:
            # Delete the task
            self.db.delete_task(int(task_id))

            # Cancel any pending nudge and reschedule
            if self.nudge_task and not self.nudge_task.done():
                self.nudge_task.cancel()
            self.nudge_task = self.loop.create_task(self.nudge_user())

    async def listen(self):
        """Override the base listen method to handle legacy formats."""
        try:
            while True:
                # First try to receive as JSON
                try:
                    data = await self.websocket.receive_json()

                    # Handle complete_task requests which use 'type' instead of 'kind'
                    if data.get('type') == 'complete_task':
                        await self.complete_task_handler(data)
                        continue

                    # Handle normal messages with 'kind'
                    if "kind" not in data:
                        await self.send_json({
                            "type": "error",
                            "error": f"Invalid message format, got keys: {' ,'.join(data.keys())}",
                        })
                    elif hasattr(self, f"{data['kind']}_handler"):
                        handler = getattr(self, f"{data['kind']}_handler")
                        await handler(data)
                    else:
                        await self.send_json({
                            "type": "error",
                            "error": f"Invalid message type: {data['kind']}",
                        })

                except Exception:
                    # If JSON parsing fails, try as plain text (legacy format)
                    data = await self.websocket.receive_text()

                    # Cancel any pending nudge
                    if self.nudge_task and not self.nudge_task.done():
                        self.nudge_task.cancel()

                    # Show typing indicator
                    await self.send_json(CommandModel(command="typing"))

                    # Process the message
                    response = await self.agent.send_prompt(data)

                    # Send the response
                    await self.send_json(ReplyModel(reply=response))

                    # Schedule next nudge
                    self.nudge_task = self.loop.create_task(self.nudge_user())

        except Exception as e:
            self.logger.exception("Error in Flowstate chat websocket: %s", str(e))
        finally:
            if self.nudge_task and not self.nudge_task.done():
                self.nudge_task.cancel()
            if self.websocket.application_state != WebSocketState.DISCONNECTED:
                await self.websocket.close()


async def flowstate_chat_websocket(websocket: WebSocket):
    """
    Entry point for the Flowstate chat WebSocket.

    Args:
        websocket: The WebSocket connection
    """
    await FlowstateChat.create_chat(websocket)
