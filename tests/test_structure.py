import os
import pytest

def test_directory_structure():
    """Test that all required directories exist in the project structure."""
    # Define the base directory for the project
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # Check main app directory structure
    assert os.path.isdir(os.path.join(base_dir, "app"))
    assert os.path.isdir(os.path.join(base_dir, "app", "api"))
    assert os.path.isdir(os.path.join(base_dir, "app", "core"))
    assert os.path.isdir(os.path.join(base_dir, "app", "db"))
    assert os.path.isdir(os.path.join(base_dir, "app", "models"))
    assert os.path.isdir(os.path.join(base_dir, "app", "schemas"))
    
    # Check key files exist
    assert os.path.isfile(os.path.join(base_dir, "app", "main.py"))
    assert os.path.isfile(os.path.join(base_dir, "app", "core", "config.py"))
    assert os.path.isfile(os.path.join(base_dir, "app", "db", "session.py"))
    assert os.path.isfile(os.path.join(base_dir, "requirements.txt"))
    assert os.path.isfile(os.path.join(base_dir, "docker-compose.yml"))
    
    # Check package initialization files exist
    assert os.path.isfile(os.path.join(base_dir, "app", "__init__.py"))
    assert os.path.isfile(os.path.join(base_dir, "app", "api", "__init__.py"))
    assert os.path.isfile(os.path.join(base_dir, "app", "core", "__init__.py"))
    assert os.path.isfile(os.path.join(base_dir, "app", "db", "__init__.py"))
    assert os.path.isfile(os.path.join(base_dir, "app", "models", "__init__.py"))
    assert os.path.isfile(os.path.join(base_dir, "app", "schemas", "__init__.py"))

def test_requirements_content():
    """Test that requirements.txt contains all necessary packages."""
    # Define the base directory for the project
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # Read requirements.txt
    with open(os.path.join(base_dir, "requirements.txt"), "r") as f:
        requirements = f.read()
    
    # Check for key packages
    essential_packages = [
        "fastapi", 
        "uvicorn", 
        "sqlalchemy", 
        "alembic", 
        "psycopg2-binary", 
        "pydantic"
    ]
    
    for package in essential_packages:
        assert package in requirements, f"{package} not found in requirements.txt"
