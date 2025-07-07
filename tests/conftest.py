
import os
os.environ["AUTH0_DOMAIN"] = "test-auth0-domain.auth0.com"
os.environ["AUTH0_API_AUDIENCE"] = "test-api-audience"
os.environ["AUTH0_JWKS"] = '{"keys": [{"alg": "RS256", "kty": "RSA", "use": "sig", "kid": "testkey", "n": "testn", "e": "AQAB"}]}'
import time
import pytest
import jose.jwt as jwt_mod
from jose import JWTError
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import docker
from app.main import app
from app.db.session import Base

# Patch jose.jwt.decode globally for all tests before app import
@pytest.fixture(scope="session", autouse=True)
def patch_jwt_decode_session():
    mp = pytest.MonkeyPatch()
    def mock_jwt_decode(token, key, algorithms, audience, issuer):
        if token == "invalid.token":
            raise JWTError("Invalid token")
        return {
            "sub": "auth0|testuser",
            "aud": audience,
            "iss": issuer,
            "email": "testuser@example.com"
        }
    def mock_get_unverified_header(token):
        if token == "invalid.token":
            raise JWTError("Invalid token header")
        return {"alg": "RS256", "typ": "JWT", "kid": "testkey"}
    mp.setattr(jwt_mod, "decode", mock_jwt_decode)
    mp.setattr(jwt_mod, "get_unverified_header", mock_get_unverified_header)
    yield
    mp.undo()

# Container configuration
POSTGRES_TEST_DB = "expense_test_db"
POSTGRES_TEST_USER = "expense_test_user"
POSTGRES_TEST_PASSWORD = "expense_test_password"
POSTGRES_TEST_PORT = "5433"  # Use a different port from the main app

# Test database URL
TEST_DATABASE_URL = f"postgresql://{POSTGRES_TEST_USER}:{POSTGRES_TEST_PASSWORD}@localhost:{POSTGRES_TEST_PORT}/{POSTGRES_TEST_DB}"

# Create a test client for FastAPI
@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client

# PostgreSQL Docker container fixture
@pytest.fixture(scope="session")
def postgres_container():
    """Start a PostgreSQL container for testing and clean up when done"""
    client = docker.from_env()
    print("Starting PostgreSQL container for testing...")
    client.images.pull("postgres:16")
    container = client.containers.run(
        "postgres:16",
        name="expense_test_db",
        detach=True,
        auto_remove=True,
        environment={
            "POSTGRES_USER": POSTGRES_TEST_USER,
            "POSTGRES_PASSWORD": POSTGRES_TEST_PASSWORD,
            "POSTGRES_DB": POSTGRES_TEST_DB,
        },
        ports={
            "5432/tcp": POSTGRES_TEST_PORT
        }
    )
    time.sleep(2)
    is_ready = False
    retry_count = 0
    max_retries = 10
    while not is_ready and retry_count < max_retries:
        try:
            test_engine = create_engine(TEST_DATABASE_URL)
            test_engine.connect().close()
            is_ready = True
            print("Successfully connected to PostgreSQL container")
        except Exception:
            retry_count += 1
            print(f"Waiting for PostgreSQL to be ready... ({retry_count}/{max_retries})")
            time.sleep(1)
    if not is_ready:
        container.stop()
        raise Exception("PostgreSQL container failed to become ready")
    print("PostgreSQL test container is ready")
    container_info = {
        "container": container,
        "db_url": TEST_DATABASE_URL,
        "db_name": POSTGRES_TEST_DB,
        "user": POSTGRES_TEST_USER,
        "password": POSTGRES_TEST_PASSWORD,
        "port": POSTGRES_TEST_PORT
    }
    yield container_info
    print("Stopping PostgreSQL test container...")
    container.stop()
    print("PostgreSQL test container stopped")

# Test database engine fixture using container
@pytest.fixture(scope="session")
def test_db_engine(postgres_container):
    """Create a SQLAlchemy engine connected to the test PostgreSQL container"""
    db_url = postgres_container["db_url"]
    engine = create_engine(db_url)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Drop all tables after tests
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Creates a new database session for each test function, using scoped_session for sharing."""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    Session = scoped_session(session_factory)
    session = Session()
    
    yield session
    
    # Clean up
    session.close()
    Session.remove()
    transaction.rollback()
    connection.close()
