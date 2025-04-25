"""Base WebSocket chat implementation that supports simple handler implementation."""
import asyncio
from asyncio import Task
from dataclasses import asdict
from typing import Any, Protocol, runtime_checkable, TYPE_CHECKING

from starlette.websockets import WebSocket, WebSocketState


if TYPE_CHECKING:
    from _typeshed import DataclassInstance


@runtime_checkable
class SupportsToDict(Protocol):
    def to_dict(self):
        ...


@runtime_checkable
class SupportsDict(Protocol):
    def dict(self):
        ...


class BaseChat:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.loop = asyncio.get_running_loop()

    async def on_connect(self):
        return

    async def listen(self):
        try:
            while True:
                data = await self.websocket.receive_json()
                if "kind" not in data:
                    self.send_json(
                        {
                            "type": "error",
                            "error": f"Invalid message format, got keys: {' ,'.join(data.keys())}",
                        }
                    )
                elif hasattr(self, f"{data['kind']}_handler"):
                    handler = getattr(self, f"{data['kind']}_handler")
                    self.loop.create_task(handler(data))
                else:
                    self.send_json(
                        {
                            "type": "error",
                            "error": f"Invalid message type: {data['kind']}",
                        }
                    )
        finally:
            if self.websocket.application_state != WebSocketState.DISCONNECTED:
                await self.websocket.close()

    def send_json(self, payload: "dict | SupportsDict | SupportsToDict | DataclassInstance") -> Task[Any]:
        return self.loop.create_task(
            self.websocket.send_json(self._to_dict(payload))
        )

    def _to_dict(self, obj) -> dict:
        match obj:
            case dict():
                return obj

            case SupportsToDict():
                return obj.to_dict()

            case SupportsDict():
                return obj.dict()

            case _:
                return asdict(obj)


    @classmethod
    async def create_chat(cls, websocket):
        await websocket.accept()
        chat = cls(websocket)
        chat.loop.create_task(chat.on_connect())
        await chat.listen()