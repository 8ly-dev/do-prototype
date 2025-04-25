"""
This package contains the WebSocket handlers for the Flowstate application.

It defines the functions that handle WebSocket connections for chat functionality
and the learn more page.
"""

from flowstate.chats.tasks import chat_websocket
from flowstate.chats.learn_more import LearnMoreChat
from flowstate.chats.utils import clean_response