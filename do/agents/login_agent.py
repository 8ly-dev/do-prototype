"""
This module contains the LoginAgent class for handling user authentication.
"""

from do.agents.base_agent import Agent
from do.db_models import get_db, User
from do.auth import generate_access_token


class LoginAgent(Agent):
    """You are the welcoming presence for Do, a human-first task management tool designed to feel like an
    innate extension of the user. Your purpose is to provide a warm, friendly welcome to users as they log in
    to the application.

    Do is the first app from 8ly, a company dedicated to creating tools that are "innately you, innately human."

    Guidelines:
    - Never refer to yourself as an AI, agent, or assistant. Do not mention automation or technical processes.
    - Don't talk about Do as an app, use the name Do instead.
    - Respond and act in a way that feels intuitive, supportive, and innately human.
    - Keep your welcome messages brief, warm, and encouraging.
    - If this is a new user, make them feel especially welcome.
    - If this is a returning user, acknowledge their return in a natural way.

    Tone:
    Natural, warm, and friendly. Always prioritize making the user feel welcome and comfortable."""

    def __init__(self, websocket=None):
        self._websocket = websocket
        self._db = get_db()
        super().__init__()

    async def authenticate_user(self, username: str) -> str:
        """
        Authenticate a user by username.
        
        This method either finds an existing user or creates a new one,
        then sends an access token to the user.
        
        Args:
            username: The username to authenticate
            
        Returns:
            A dictionary with the authentication result
        """
        if not username or len(username.strip()) < 3:
            return "Invalid username"
            
        user = self._db.get_user_by_username(username)
        is_new_user = user is None
        if is_new_user:
            user_id = self._db.insert_user(username)
            user = self._db.get_user_by_id(user_id)

        # Generate an access token
        token = generate_access_token(user.id)
        await self._websocket.send_json(
            {
                "kind": "command",
                "command": "login_success",
                "token": token,
            }
        )
        
        return f"{user.username} authenticated, giving access in 5 seconds"
