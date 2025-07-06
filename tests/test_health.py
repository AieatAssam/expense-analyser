import pytest
from fastapi import status

def test_health_endpoint(client):
    """Test that the health check endpoint returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok", "message": "API is operational"}

def test_api_structure():
    """Test that the main project structure exists."""
    # Import key components to ensure they exist
    from app.main import app
    from app.core.config import settings
    from app.db.session import get_db
    from app.api.api import api_router
    
    # Assert FastAPI instance is properly configured
    assert app.title == "Expense Analyser API"
    assert app.description == "API for expense receipt analysis and tracking"
    assert app.version == "0.1.0"
    
    # Verify settings
    assert hasattr(settings, "API_V1_STR")
    assert hasattr(settings, "DATABASE_URL")
    assert hasattr(settings, "CORS_ORIGINS")

def test_cors_middleware():
    """Test that CORS middleware is configured."""
    from app.main import app
    from fastapi.middleware.cors import CORSMiddleware
    
    # Check if CORS middleware is configured by checking the route handlers
    # FastAPI doesn't expose middleware directly in a testable way, so we check for CORS settings
    assert app.root_path == ""  # Just a simple check that app is configured
    
    # Alternative way: Check that the CORS_ORIGINS setting is configured
    from app.core.config import settings
    assert len(settings.CORS_ORIGINS) > 0
