"""
This module contains agent classes for the Do application.

The agents are responsible for handling user requests, interacting with the database,
and generating responses using language models. Each agent is specialized for a specific
task, such as managing tasks, generating email content, or providing information about
the application.
"""

from do.agents.base_agent import Agent
from do.agents.email_agent import EmailAgent, EmailHelperSuggestions
from do.agents.do_agent import DoAgent
from do.agents.learn_more_agent import LearnMoreAgent
from do.agents.login_agent import LoginAgent
from do.agents.suggested_actions_agent import LearnMoreSuggestedActionsAgent, SuggestedActions
from do.agents.models import LLMSettings
from do.agents.utils import get_model, get_small_model