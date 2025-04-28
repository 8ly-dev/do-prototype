"""
This module contains the WebSocket handler for the login page.
"""

import asyncio
from dataclasses import dataclass
from typing import Literal, TypedDict

from starlette.websockets import WebSocket

from flowstate.agents import LoginAgent
from flowstate.chats.base_chat import BaseChat
from flowstate.utils.messages import get_random_welcome_message


class PromptData(TypedDict):
    kind: Literal["prompt"]
    prompt: str


@dataclass
class CommandModel:
    command: str
    kind: Literal["command"] = "command"


@dataclass
class ReplyModel:
    reply: str
    kind: Literal["reply"] = "reply"


@dataclass
class LoginSuccessModel:
    token: str
    redirect_url: str = "/"
    command: Literal["login_success"] = "login_success"
    kind: Literal["command"] = "command"


class LoginChat(BaseChat):
    def __init__(self, websocket: WebSocket):
        super().__init__(websocket)
        self.agent = LoginAgent(websocket)

    async def on_connect(self):
        # Get a random welcome message
        welcome_message = get_random_welcome_message()

        # Send welcome message
        await self.send_json(ReplyModel(
            reply=welcome_message
        ))

    async def prompt_handler(self, data: PromptData):
        await self.send_json(CommandModel(command="typing"))
        response = await self.agent.send_prompt(data["prompt"])
        await self.send_json(ReplyModel(reply=response))
