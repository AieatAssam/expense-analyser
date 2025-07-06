import pytest
from fastapi.testclient import TestClient

from app.main import app

# Create a test client for FastAPI
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client
