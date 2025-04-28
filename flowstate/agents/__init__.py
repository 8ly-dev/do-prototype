"""
This module contains agent classes for the Flowstate application.

The agents are responsible for handling user requests, interacting with the database,
and generating responses using language models. Each agent is specialized for a specific
task, such as managing tasks, generating email content, or providing information about
the application.
"""

from flowstate.agents.base_agent import Agent
from flowstate.agents.email_agent import EmailAgent, EmailHelperSuggestions
from flowstate.agents.flowstate_agent import FlowstateAgent
from flowstate.agents.learn_more_agent import LearnMoreAgent
from flowstate.agents.login_agent import LoginAgent
from flowstate.agents.suggested_actions_agent import LearnMoreSuggestedActionsAgent, SuggestedActions
from flowstate.agents.models import LLMSettings
from flowstate.agents.utils import get_model, get_small_model