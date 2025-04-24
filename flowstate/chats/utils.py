"""
This module contains utility functions for the chat functionality.
"""

import re


def clean_response(response: str) -> str:
    """
    Clean the response text by ensuring there's a space before "8ly".

    This function adds a space before "8ly" if there isn't already a space before it,
    to ensure proper formatting in the response text.

    Args:
        response: The response text to clean

    Returns:
        The cleaned response text
    """
    return re.sub(r'([^\s\-_"\'./\\])(8ly)', r'\g<1> \g<2>', response)