"""
This module contains utility functions for the agents.
"""

from typing import Literal

from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

from flowstate.agents.models import LLMSettings
from flowstate.secrets import get_secrets

_model = None
_small_model = None


def get_model():
    """
    Get or initialize the language model.

    Returns:
        A configured GeminiModel instance using settings from secrets.
    """
    global _model
    if _model is None:
        _model = _create_model("large")

    return _model


def get_small_model():
    """
    Get or initialize the small language model.

    Returns:
        A configured GeminiModel instance using settings from secrets.
    """
    global _small_model
    if _small_model is None:
        _small_model = _create_model("small")

    return _small_model


def _create_model(size: Literal["large", "small"] = "large"):
    llm_settings = get_secrets("llm-settings", LLMSettings)
    return GeminiModel(
        llm_settings.model if size == "large" else llm_settings.small_model,
        provider=GoogleGLAProvider(
            api_key=llm_settings.google_token
        )
    )