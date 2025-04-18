from contextlib import contextmanager

from fastapi import Depends, HTTPException, status, Request, Cookie, Header

from flowstate.db_models import FlowstateDB, User


@contextmanager
def get_db() -> FlowstateDB:
    db = FlowstateDB()  # Replace with your actual database connection
    try:
        yield db
    finally:
        db.conn.close()


async def get_current_user(
    token: str = Header(default=None, alias="Access-Token"),
    db: FlowstateDB = Depends(get_db)
) -> User | None:
    email = verify_hmac_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    user = db.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user