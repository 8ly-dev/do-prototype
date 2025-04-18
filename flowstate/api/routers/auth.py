import asyncio
import os
from contextlib import suppress

from fastapi import APIRouter, Depends, Response
from flowstate.dependencies import get_db
from flowstate.auth import generate_login_token, verify_login_token, generate_access_token


SECRET_KEY = os.environ.get("SECRET_KEY", "default_secret_key")

router = APIRouter()


@router.post("/login", response_model=dict)
async def request_login_link(email: str, db=Depends(get_db)):
    with suppress(Exception):
        asyncio.get_running_loop().run_in_executor(None, send_login_email, email.lower(), SECRET_KEY)

    return {"message": "Login link sent to email"}


@router.get("/verify")
async def verify_login_token(token: str, db=Depends(get_db)):
    """
    Verify the login token and return an access token.
    """
    email = verify_login_token(token, SECRET_KEY)
    if not email:
        return Response(status_code=401, content={"error": "Invalid token"})

    user = db.get_user_by_email(email)
    user_id = user.id if user else db.insert_user(email)
    return {"access_token": generate_access_token(user_id, SECRET_KEY)}
