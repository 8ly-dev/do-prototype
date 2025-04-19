import base64
import hmac
from contextlib import suppress
from datetime import datetime, UTC

import flowstate.secrets
from flowstate.emails import Email, send_email, Sender


def send_auth_email(email: str, secret_key: str):
    """Send an email with a login token."""
    token = generate_login_token(email, secret_key)
    sender = flowstate.secrets.get_secrets("email", Sender)
    email = Email(
        to=email,
        subject="Login to Flowstate",
        body=f"Hi! Login with this link: http://localhost:8000/login?t={token}",
    )
    send_email(email, sender)


def generate_login_token(email: str, secret_key: str) -> str:
    """Generate a HMAC-signed login token that's base64-encoded."""
    signature = hmac.new(secret_key.encode(), email.encode(), "sha256").hexdigest()
    payload = f"{email}{signature}".encode()
    return base64.urlsafe_b64encode(payload).decode()


def generate_access_token(user_id: int, secret_key: str) -> str:
    """Generate a HMAC-signed access token that's base64-encoded."""
    timestamp = datetime.now(UTC).isoformat()
    signature = generate_access_token_signature(user_id, timestamp, secret_key)
    payload = user_id.to_bytes(8, "big") + timestamp.encode() + signature.encode()
    return base64.urlsafe_b64encode(payload).decode()


def generate_access_token_signature(user_id: int, timestamp: str, secret_key: str) -> str:
    body = user_id.to_bytes(8, "big") + timestamp.encode()
    return hmac.new(secret_key.encode(), body, "sha256").hexdigest()


def verify_login_token(token: str, secret_key: str) -> str | None:
    """Verify a login token."""
    with suppress(ValueError, TypeError):
        payload = base64.urlsafe_b64decode(token).decode()
        email, signature = payload[:-64], payload[-64:]
        expected_signature = hmac.new(secret_key.encode(), email.encode(), "sha256").hexdigest()
        return email if signature == expected_signature else None

    return None


def verify_access_token(token: str, secret_key: str) -> int | None:
    """Verify an access token."""
    with suppress(ValueError, TypeError):
        payload = base64.urlsafe_b64decode(token)
        user_id_bytes, timestamp_bytes, signature_bytes = payload[:8], payload[8:-64], payload[-64:]
        user_id = int.from_bytes(user_id_bytes, "big")
        timestamp = timestamp_bytes.decode()
        signature = signature_bytes.decode()
        expected_signature = generate_access_token_signature(user_id, timestamp, secret_key)
        return user_id if signature == expected_signature else None

    return None
