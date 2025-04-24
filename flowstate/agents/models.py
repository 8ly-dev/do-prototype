"""
This module contains model classes used by the agents.
"""

from dataclasses import dataclass


@dataclass
class LLMSettings:
    """
    Settings for language model configuration.

    Attributes:
        groq_token: API token for Groq
        google_token: API token for Google
        openai_token: API token for OpenAI
        model: Name of the language model to use
        small_model: Name of the small language model to use
    """
    groq_token: str
    google_token: str
    openai_token: str
    model: str
    small_model: str