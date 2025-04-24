"""
This module contains the LearnMoreSuggestedActionsAgent class for suggesting actions to the user.
"""

from pydantic import BaseModel as PydanticModel, Field as PydanticField

from flowstate.agents.base_agent import Agent
from flowstate.agents.utils import get_small_model


class SuggestedActions(PydanticModel):
    """Three suggested actions for the user to take."""
    action_1: str = PydanticField(description="The first suggested action.")
    action_2: str = PydanticField(description="The second suggested action.")
    action_3: str = PydanticField(description="The third suggested action.")

    def to_list(self) -> list[str]:
        """
        Convert the suggested actions to a list.

        Returns:
            A list containing the three suggested actions
        """
        return [
            action.strip(" .")
            for action in [self.action_1, self.action_2, self.action_3]
            if action
        ]


class LearnMoreSuggestedActionsAgent(Agent[None, SuggestedActions]):
    """You'll be given messages in a conversation between USER and AGENT. In this conversation AGENT is representing a
    pre-seed startup (8ly) that is seeking both co-founders and financial backers. USER is either a potential
    co-founder or financial backer attempting to evaluate 8ly and it's app, Flowstate. Based on the conversation,
    provide 3 guesses as to what the USER might ask next.

    Have a mindset of exploration, outside the box, digging deeper. Don't ask the same generic questions. Possible
    areas of interest to the USER:
    - Prototype codebase (co-founders especially)
    - Funding
    - Timelines
    - Team
    - Features

    Guidelines:
    - Questions should be 8 to 12 words
    - Questions should never refer to AGENT, only the app or startup
    - Guesses MUST BE QUESTIONS, never guess that they'll make a statement
    """
    agent_factory = lambda _: get_small_model()
    output_type = SuggestedActions