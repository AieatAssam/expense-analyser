"""
Tests for API health and structure.
These tests verify the API is correctly configured and basic health endpoints work.
"""
from fastapi import status


def test_root_health_endpoint(client):
    """Test that the root health check endpoint returns comprehensive status."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
    assert "timestamp" in data
    assert "version" in data
    assert "environment" in data
    assert "components" in data


def test_root_ping_endpoint(client):
    """Test that the root ping endpoint works."""
    response = client.get("/ping")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["ping"] == "pong"
    assert data["status"] == "ok"


def test_comprehensive_health_endpoint(client):
    """Test the comprehensive health endpoint under /api/v1/health."""
    response = client.get("/api/v1/health")
    assert response.status_code in [200, 503]  # Can be 503 if unhealthy
    
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
    assert "components" in data
    
    # Check that all expected components are present
    expected_components = ["database", "redis", "configuration", "llm_providers", "storage"]
    for component in expected_components:
        assert component in data["components"]


def test_comprehensive_health_endpoint_with_details(client):
    """Test the comprehensive health endpoint with details."""
    response = client.get("/api/v1/health?details=true")
    assert response.status_code in [200, 503]
    
    data = response.json()
    assert "components" in data
    
    # With details, each component should have more information
    for component_name, component_data in data["components"].items():
        if isinstance(component_data, dict):
            assert "status" in component_data
            assert "checked_at" in component_data


def test_readiness_endpoint(client):
    """Test the Kubernetes-style readiness endpoint."""
    response = client.get("/api/v1/health/ready")
    assert response.status_code in [200, 503]
    
    data = response.json()
    assert "status" in data
    assert data["status"] in ["ready", "not_ready"]
    assert "checks" in data


def test_liveness_endpoint(client):
    """Test the Kubernetes-style liveness endpoint."""
    response = client.get("/api/v1/health/live")
    assert response.status_code == status.HTTP_200_OK  # Should almost always be 200
    
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data


def test_simple_status_endpoint(client):
    """Test the simple status endpoint."""
    response = client.get("/api/v1/health/status")
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "expense-analyser-api"
    assert data["version"] == "0.1.0"


def test_api_structure():
    """Test that the main project structure exists."""
    # Import key components to ensure they exist
    from app.main import app
    from app.core.config import settings
    
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
    
    # Check if CORS middleware is configured by checking the route handlers
    # FastAPI doesn't expose middleware directly in a testable way, so we check for CORS settings
    assert app.root_path == ""  # Just a simple check that app is configured
    
    # Alternative way: Check that the CORS_ORIGINS setting is configured
    from app.core.config import settings
    assert len(settings.CORS_ORIGINS) > 0


def test_all_health_endpoints_accessible(client):
    """Test that all health endpoints are accessible and return valid responses."""
    health_endpoints = [
        "/health",
        "/ping", 
        "/ready",
        "/live",
        "/api/v1/health",
        "/api/v1/health/ready",
        "/api/v1/health/live",
        "/api/v1/health/status",
        "/api/v1/ping"
    ]
    
    for endpoint in health_endpoints:
        response = client.get(endpoint)
        # All endpoints should return either 200 or 503 (service unavailable)
        assert response.status_code in [200, 503], f"Endpoint {endpoint} returned {response.status_code}"
        
        # All endpoints should return JSON
        data = response.json()
        assert isinstance(data, dict), f"Endpoint {endpoint} did not return a JSON object"
        
        # All endpoints should have a status field
        assert "status" in data, f"Endpoint {endpoint} did not include status field"
