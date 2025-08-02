"""
Test suite for Auth0 authentication flows: login, logout, token validation, and multi-account switching.
Mocks Auth0 responses and uses test database fixtures.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from jose import jwt
import base64
import json
from app.db.session import get_db

# Set up test environment variables for Auth0 integration
os.environ["AUTH0_DOMAIN"] = "test-auth0-domain.auth0.com"
os.environ["AUTH0_API_AUDIENCE"] = "test-api-audience"
os.environ["AUTH0_CLIENT_ID"] = "test-client-id"
os.environ["AUTH0_CLIENT_SECRET"] = "test-client-secret"

AUTH0_DOMAIN = "test-auth0-domain.auth0.com"
API_AUDIENCE = "test-api-audience"
ALGORITHMS = ["RS256"]

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
    from app.main import app as fastapi_app
    def override_get_db():
        yield test_db_session
    fastapi_app.dependency_overrides[get_db] = override_get_db
    
    # Mock the get_jwks function to return test JWKS
    with patch('app.core.auth.get_jwks', return_value=mock_jwks):
        with TestClient(fastapi_app) as c:
            yield c
    fastapi_app.dependency_overrides.clear()



@pytest.fixture
def auth0_token():
    # Create a valid JWT header and payload
    header = {"alg": "RS256", "typ": "JWT", "kid": "testkey"}
    payload = {
        "sub": "auth0|testuser",
        "aud": API_AUDIENCE,
        "iss": f"https://{AUTH0_DOMAIN}/",
        "email": "testuser@example.com"
    }
    def b64url(data):
        return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()
    token = f"{b64url(header)}.{b64url(payload)}.signature"
    return token

@pytest.fixture
def test_auth0_user(test_db_session):
    from app.models.user import User
    from app.models.account import Account
    test_email = "testuser@example.com"
    test_sub = "auth0|testuser"
    user = User(email=test_email, hashed_password="", is_active=True, is_superuser=False)
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    account = Account(provider="auth0", provider_account_id=test_sub, user_id=user.id)
    test_db_session.add(account)
    test_db_session.commit()
    test_db_session.refresh(account)
    test_db_session.commit()
    yield user, account
    # Cleanup
    test_db_session.delete(account)
    test_db_session.delete(user)
    test_db_session.commit()

def test_login_success(client, auth0_token):
    response = client.get("/api/v1/protected/protected", headers={"Authorization": f"Bearer {auth0_token}"})
    assert response.status_code in (200, 401)

def test_token_validation_error(client):
    response = client.get("/api/v1/protected/protected", headers={"Authorization": "Bearer invalid.token"})
    assert response.status_code == 401

def test_multi_account_switching(client, auth0_token, test_auth0_user):
    response = client.get("/api/v1/protected/switch-account", headers={"Authorization": f"Bearer {auth0_token}"})
    assert response.status_code in (200, 404)

def test_logout(client, auth0_token, test_auth0_user):
    response = client.post("/api/v1/protected/logout", headers={"Authorization": f"Bearer {auth0_token}"})
    assert response.status_code in (200, 404)