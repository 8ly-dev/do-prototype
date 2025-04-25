"""
This module contains the WebSocket handler for the learn more page.
"""

import asyncio
from dataclasses import dataclass
from typing import Literal, TypedDict

import pydantic_ai

from flowstate.agents import LearnMoreAgent, LearnMoreSuggestedActionsAgent
from flowstate.auth import verify_access_token
from flowstate.chats.base_chat import BaseChat
from flowstate.db_models import get_db, User
from flowstate.chats.utils import clean_response


class PromptData(TypedDict):
    kind: Literal["prompt"]
    prompt: str


@dataclass
class ActionModel:
    actions: list[str]
    kind: Literal["action"] = "action"


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


class LearnMoreChat(BaseChat):
    def __init__(self, websocket):
        super().__init__(websocket)
        self.user = self._get_user()
        self.agent = LearnMoreAgent(self.user, self)
        self.suggestion_agent = LearnMoreSuggestedActionsAgent()
        self._message_counter = 0
        self._pending_tasks = []

    async def on_connect(self):
        # Let the user know we're connected
        name = f" {self.user.username}" if self.user else ""
        await self.send_json(CommandModel(command="typing"))
        await self.send_json(
            UsingModel(tool_message=f"Hi{name}, one moment please")
        )

        # Get the suggested questions
        actions, _ = await asyncio.gather(
            self.suggestion_agent.send_prompt(f"AGENT:\n{self.agent.readme}"),
            asyncio.sleep(2),
        )

        # Send the readme and the actions
        await self.send_json(ReplyModel(reply=self.agent.readme))
        await self.send_json(ActionModel(actions=actions.to_list()))

    async def prompt_handler(self, data: PromptData):
        self._cancel_pending_tasks()
        self._message_counter += 1
        try:
            response = await self.agent.send_prompt(data["prompt"])
        except pydantic_ai.exceptions.ModelHTTPError:
            await self.send_json(
                ReplyModel(reply="I'm sorry, something went wrong. Please try again in a moment.")
            )
            await self.send_json(CommandModel(command="reload"))
            raise
        else:
            response = clean_response(response)
            self.send_json(ReplyModel(reply=response))
            self._pending_tasks.append(
                self.loop.create_task(
                    self._send_suggested_actions(
                        f"USER:\n{data}\n"
                        f"AGENT:\n{response}\n"
                    )
                )
            )

    async def send_using(self, using_message: str):
        self.send_json(UsingModel(tool_message=using_message))

    def _cancel_pending_tasks(self):
        for task in self._pending_tasks:
            task.cancel()

        self._pending_tasks.clear()

    def _get_user(self) -> User | None:
        token = self.websocket.cookies.get("SESSION_TOKEN")
        if not token:
            return None

        user_id = verify_access_token(token)
        if user_id is None:
            return None

        return get_db().get_user_by_id(user_id)

    async def _send_suggested_actions(self, prompt: str):
        try:
            suggested_actions = await self.suggestion_agent.send_prompt(prompt)
        except pydantic_ai.exceptions.ModelHTTPError:
            await self.send_json(
                ReplyModel(reply="I'm sorry, something went wrong. Please try again in a moment.")
            )
            await self.send_json(CommandModel(command="reload"))
            raise
        else:
            if suggested_actions:
                await self.websocket.send_json(self._to_dict(ActionModel(actions=suggested_actions.to_list())))
