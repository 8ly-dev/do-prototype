"""
Authentication utilities for the Do application.

This module provides functions for generating and verifying access tokens
used for user authentication.
"""

import base64
import hmac
from contextlib import suppress
from datetime import datetime, UTC

import do.configs


SECRET_KEY: bytes = do.secrets.get_secret(
    "secret-key",
    default="default-secret-please-configure"
).encode()


def generate_access_token(user_id: int) -> str:
    """
    Generate a HMAC-signed access token for a user.

    This function creates a token containing the user ID and a timestamp,
    signs it with HMAC using the secret key, and encodes it in base64.

    Args:
        user_id: The ID of the user to generate a token for

    Returns:
        A base64-encoded access token
    """
    timestamp = datetime.now(UTC).isoformat()
    signature = generate_access_token_signature(user_id, timestamp)
    payload = user_id.to_bytes(8, "big") + timestamp.encode() + signature.encode()
    return base64.urlsafe_b64encode(payload).decode()


def generate_access_token_signature(user_id: int, timestamp: str) -> str:
    """
    Generate a signature for an access token.

    This function creates an HMAC signature using the secret key and the
    user ID and timestamp as the message.

    Args:
        user_id: The ID of the user
        timestamp: The timestamp as an ISO-formatted string

    Returns:
        A hexadecimal HMAC signature
    """
    body = user_id.to_bytes(8, "big") + timestamp.encode()
    return hmac.new(SECRET_KEY, body, "sha256").hexdigest()


def verify_access_token(token: str) -> int | None:
    """
    Verify an access token and extract the user ID.

    This function decodes the token, extracts the user ID, timestamp, and signature,
    verifies the signature, and returns the user ID if the signature is valid.

    Args:
        token: The access token to verify

    Returns:
        The user ID if the token is valid, or None if the token is invalid
    """
    with suppress(ValueError, TypeError):
        payload = base64.urlsafe_b64decode(token)
        user_id_bytes, timestamp_bytes, signature_bytes = payload[:8], payload[8:-64], payload[-64:]
        user_id = int.from_bytes(user_id_bytes, "big")
        timestamp = timestamp_bytes.decode()
        signature = signature_bytes.decode()
        expected_signature = generate_access_token_signature(user_id, timestamp)
        return user_id if signature == expected_signature else None

    return None
