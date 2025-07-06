import os
import yaml

def test_docker_compose_configuration():
    """Test that docker-compose.yml is properly configured."""
    # Define the base directory for the project
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # Read docker-compose.yml
    with open(os.path.join(base_dir, "docker-compose.yml"), "r") as f:
        docker_compose = yaml.safe_load(f)
    
    # Check for required services
    assert "db" in docker_compose["services"], "PostgreSQL service not found in docker-compose.yml"
    assert "api" in docker_compose["services"], "API service not found in docker-compose.yml"
    
    # Check PostgreSQL configuration
    db_service = docker_compose["services"]["db"]
    assert db_service["image"] == "postgres:16", "PostgreSQL image should be version 16"
    assert "POSTGRES_USER" in db_service["environment"], "POSTGRES_USER environment variable not set"
    assert "POSTGRES_PASSWORD" in db_service["environment"], "POSTGRES_PASSWORD environment variable not set"
    assert "POSTGRES_DB" in db_service["environment"], "POSTGRES_DB environment variable not set"
    
    # Check API configuration
    api_service = docker_compose["services"]["api"]
    assert "build" in api_service, "API service build configuration not found"
    assert api_service["depends_on"]["db"]["condition"] == "service_healthy", "API should depend on healthy DB service"
    assert "DATABASE_URL" in api_service["environment"], "DATABASE_URL environment variable not set"
    assert "uvicorn" in api_service["command"], "API service command should use uvicorn"
