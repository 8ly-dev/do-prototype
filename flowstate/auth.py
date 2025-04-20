import base64
import hmac
from contextlib import suppress
from datetime import datetime, UTC

import flowstate.secrets


SECRET_KEY: bytes = flowstate.secrets.get_secret(
    "secret-key",
    default="default-secret-please-configure"
).encode()


def generate_access_token(user_id: int) -> str:
    """Generate a HMAC-signed access token that's base64-encoded."""
    timestamp = datetime.now(UTC).isoformat()
    signature = generate_access_token_signature(user_id, timestamp)
    payload = user_id.to_bytes(8, "big") + timestamp.encode() + signature.encode()
    return base64.urlsafe_b64encode(payload).decode()


def generate_access_token_signature(user_id: int, timestamp: str) -> str:
    body = user_id.to_bytes(8, "big") + timestamp.encode()
    return hmac.new(SECRET_KEY, body, "sha256").hexdigest()


def verify_access_token(token: str) -> int | None:
    """Verify an access token."""
    with suppress(ValueError, TypeError):
        payload = base64.urlsafe_b64decode(token)
        user_id_bytes, timestamp_bytes, signature_bytes = payload[:8], payload[8:-64], payload[-64:]
        user_id = int.from_bytes(user_id_bytes, "big")
        timestamp = timestamp_bytes.decode()
        signature = signature_bytes.decode()
        expected_signature = generate_access_token_signature(user_id, timestamp)
        return user_id if signature == expected_signature else None

    return None
