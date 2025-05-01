"""
Utility functions for loading and managing messages from the messages.toml file.
"""

import random
import tomllib
from pathlib import Path
from typing import List

# Cache for the loaded messages
_messages_cache = {}

def get_welcome_messages() -> List[str]:
    """
    Get the list of welcome messages from the messages.toml file.

    Returns:
        A list of welcome messages
    """
    return _get_messages_from_section("welcome-messages")

def get_random_welcome_message() -> str:
    """
    Get a random welcome message from the messages.toml file.

    Returns:
        A random welcome message
    """
    messages = get_welcome_messages()
    return random.choice(messages) if messages else "Welcome to Do! Please enter your username to continue."

def _get_messages_from_section(section: str) -> List[str]:
    """
    Get messages from a specific section of the messages.toml file.

    Args:
        section: The section name in the TOML file

    Returns:
        A list of messages from the specified section
    """
    # Check if the messages are already cached
    if section in _messages_cache:
        return _messages_cache[section]

    # Find the messages.toml file
    project_root = Path(__file__).parent.parent.parent
    messages_file = project_root / "messages.toml"

    # If the file doesn't exist, return an empty list
    if not messages_file.exists():
        return []

    try:
        # Load the TOML file
        with open(messages_file, "rb") as f:
            data = tomllib.load(f)

        # Get the messages from the specified section
        section_data = data.get(section, {})
        messages = section_data.get("messages", [])

        # Cache the messages
        _messages_cache[section] = messages

        return messages
    except Exception as e:
        print(f"Error loading messages from {messages_file}: {e}")
        return []
