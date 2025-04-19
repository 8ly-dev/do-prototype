import asyncio
from dataclasses import dataclass

from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.groq import GroqProvider
from pydantic_ai import Agent

from flowstate.secrets import get_secrets

_model = None

@dataclass
class LLMSettings:
    groq_token: str
    model: str


def get_model():
    global _model
    if _model is None:
        llm_settings = get_secrets("llm-settings", LLMSettings)
        _model = GroqModel(
            llm_settings.model,
            provider=GroqProvider(api_key=llm_settings.groq_token)
        )

    return _model


class ManagingAgent:
    def __init__(self):
        self.agent = Agent(
            get_model(),
            system_prompt=(
                """You're an extension of the user, not an LLM or chat bot. Your job is to help the user create
                projects, and tasks. Don't hold conversations, instead try to figure out how the user's conversation
                relates to the work at hand and direct them towards that goal. Don't assume what the user wants, 
                instead favor asking. Giving suggestions is good, stay focused."""
            )
        )
        self.history = []

    async def send_prompt(self, prompt: str) -> str:
        attempts = 0
        while attempts < 3:
            try:
                response = await self.agent.run(prompt, message_history=self.history)
            except Exception:
                await asyncio.sleep(0.2)
                attempts += 1
                if attempts >= 3:
                    raise
            else:
                self.history.extend(response.new_messages())
                return response.output

        raise Exception()