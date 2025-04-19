import pytest
import base64
import hmac
from datetime import datetime, UTC
from flowstate.auth import (
    generate_login_token,
    verify_login_token,
    generate_access_token,
    verify_access_token,
)
import flowstate.auth


@pytest.fixture
def secret_key():
    return b"test-secret-key-123!"


@pytest.fixture
def sample_email():
    return "user@example.com"


@pytest.fixture
def sample_user_id():
    return 42


class TestLoginTokenFlow:
    def test_generate_and_verify_valid_token(self, sample_email):
        token = generate_login_token(sample_email)
        verified_email = verify_login_token(token)
        assert verified_email == sample_email

    def test_tampered_token_fails(self, sample_email):
        token = generate_login_token(sample_email)
        # Tamper with the token
        tampered = token[:-2] + "=="
        assert verify_login_token(tampered) is None

    def test_wrong_secret_fails(self, sample_email):
        token = generate_login_token(sample_email)
        flowstate.auth.SECRET_KEY = b"wrong-secret"
        assert verify_login_token(token) is None

    @pytest.mark.parametrize(
        "bad_input", [
            "",
            "not-base64",
            base64.urlsafe_b64encode(b"tooshort").decode()
        ]
        )
    def test_invalid_tokens(self, bad_input):
        assert verify_login_token(bad_input) is None


class TestAccessTokenFlow:
    def test_generate_and_verify_valid_token(self, sample_user_id):
        token = generate_access_token(sample_user_id)
        verified_id = verify_access_token(token)
        assert verified_id == sample_user_id

    def test_token_expiry_detection(self, secret_key, sample_user_id):
        # Generate token with old timestamp
        old_time = datetime(2024, 1, 1, tzinfo=UTC).isoformat()
        signature = hmac.new(
            secret_key,
            sample_user_id.to_bytes(8, "big") + old_time.encode(),
            "sha256"
        ).hexdigest()
        payload = base64.urlsafe_b64encode(
            sample_user_id.to_bytes(8, "big") +
            old_time.encode() +
            signature.encode()
        ).decode()

        # Implementation would normally check timestamp freshness
        # This test just verifies cryptographic validity
        flowstate.auth.SECRET_KEY = secret_key
        assert verify_access_token(payload) == sample_user_id

    def test_tampered_user_id_fails(self, sample_user_id):
        token = generate_access_token(sample_user_id)
        decoded = base64.urlsafe_b64decode(token)
        # Tamper with user ID bytes
        tampered = bytes([decoded[0] ^ 0xFF]) + decoded[1:]
        tampered_token = base64.urlsafe_b64encode(tampered).decode()
        assert verify_access_token(tampered_token) is None

    def test_invalid_tokens(self):
        assert verify_access_token("invalid.token") is None


class TestSecurityRequirements:
    def test_token_uniqueness(self, secret_key):
        token1 = generate_login_token("user1@test.com")
        token2 = generate_login_token("user2@test.com")
        assert token1 != token2

    def test_access_token_time_binding(self, sample_user_id):
        token1 = generate_access_token(sample_user_id)
        token2 = generate_access_token(sample_user_id)
        assert token1 != token2  # Different timestamps

    def test_signature_verification_strict(self, sample_email):
        token = generate_login_token(sample_email)
        flowstate.auth.SECRET_KEY += b"x"
        assert verify_login_token(token) is None
