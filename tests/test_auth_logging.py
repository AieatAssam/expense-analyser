
import logging
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import get_db
from app.models.user import User
from app.models.account import Account
import io
import base64
import json

# Fixture to generate a valid Auth0 token for logging tests
@pytest.fixture
def auth0_token():
    header = {"alg": "RS256", "typ": "JWT", "kid": "testkey"}
    payload = {
        "sub": "auth0|testuser",
        "aud": "test-api-audience",
        "iss": "https://test-auth0-domain.auth0.com/",
        "email": "testuser@example.com"
    }
    def b64url(data):
        return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()
    token = f"{b64url(header)}.{b64url(payload)}.signature"
    return token

@pytest.fixture
def mock_jwks():
    """Mock JWKS response for testing"""
    return {
        "keys": [
            {
                "alg": "RS256",
                "kty": "RSA",
                "use": "sig",
                "kid": "testkey",
                "n": "testn",
                "e": "AQAB"
            }
        ]
    }

@pytest.fixture
def client(test_db_session, mock_jwks):
    def override_get_db():
        yield test_db_session
    app.dependency_overrides[get_db] = override_get_db
    
    # Mock the get_jwks function to return test JWKS
    with patch('app.core.auth.get_jwks', return_value=mock_jwks):
        with TestClient(app) as c:
            yield c
    app.dependency_overrides.clear()

@pytest.fixture
def capture_auth_logger():
    logger = logging.getLogger("auth.security")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    yield log_stream
    logger.removeHandler(handler)

# Test that successful login logs expected events
def test_auth_logging_success(client, auth0_token, capture_auth_logger):
    client.get("/api/v1/protected/protected", headers={"Authorization": f"Bearer {auth0_token}"})
    logs = capture_auth_logger.getvalue()
    assert "Auth event: Received token for validation" in logs
    assert "Auth event: JWT validated successfully for subject auth0|testuser" in logs
    assert "Auth event: Auto-created first user testuser@example.com and account" in logs

# Test that invalid token logs security incident
def test_auth_logging_invalid_token(client, capture_auth_logger):
    response = client.get("/api/v1/protected/protected", headers={"Authorization": "Bearer invalid.token"})
    logs = capture_auth_logger.getvalue()
    assert "Security incident: JWTError during token validation" in logs
    assert response.status_code == 401

# Test that unlinked account logs warning
def test_auth_logging_unlinked_account(client, capture_auth_logger):
    # Use the test_db_session from the client fixture for user creation
    test_db = client.app.dependency_overrides[get_db]().__next__()
    test_db.query(Account).delete()
    test_db.query(User).delete()
    test_db.commit()
    dummy_user = User(email="dummyuser@example.com", hashed_password="", is_active=True, is_superuser=False)
    test_db.add(dummy_user)
    test_db.commit()
    test_db.refresh(dummy_user)
    import jose.jwt as jwt_mod
    from jose import JWTError
    # Patch jwt.decode and get_unverified_header locally for this test
    orig_decode = jwt_mod.decode
    orig_get_unverified_header = jwt_mod.get_unverified_header
    def local_jwt_decode(token, key, algorithms, audience, issuer):
        if token == "invalid.token":
            raise JWTError("Invalid token")
        # Parse payload from token
        try:
            payload_b64 = token.split(".")[1]
            import base64, json
            padded = payload_b64 + '=' * (-len(payload_b64) % 4)
            payload = json.loads(base64.urlsafe_b64decode(padded).decode())
            return payload
        except Exception:
            return {
                "sub": "auth0|unknownuser",
                "aud": audience,
                "iss": issuer,
                "email": "unknownuser@example.com"
            }
    def local_get_unverified_header(token):
        if token == "invalid.token":
            raise JWTError("Invalid token header")
        return {"alg": "RS256", "typ": "JWT", "kid": "testkey"}
    jwt_mod.decode = local_jwt_decode
    jwt_mod.get_unverified_header = local_get_unverified_header
    # (Removed duplicate user/account creation)
    # Token with valid header/payload but unknown sub
    header = {"alg": "RS256", "typ": "JWT", "kid": "testkey"}
    payload = {
        "sub": "auth0|unknownuser",
        "aud": "test-api-audience",
        "iss": "https://test-auth0-domain.auth0.com/",
        "email": "unknownuser@example.com"
    }
    def b64url(data):
        return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()
    token = f"{b64url(header)}.{b64url(payload)}.signature"
    response = client.get("/api/v1/protected/protected", headers={"Authorization": f"Bearer {token}"})
    logs = capture_auth_logger.getvalue()
    assert "Security incident: Account auth0|unknownuser not linked. Invitation required." in logs
    assert response.status_code == 403
    # Restore original monkeypatch after test
    jwt_mod.decode = orig_decode
    jwt_mod.get_unverified_header = orig_get_unverified_header
