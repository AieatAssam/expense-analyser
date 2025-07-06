import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import docker

from app.main import app
from app.db.session import Base

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
    
    # Pull the PostgreSQL image if needed
    client.images.pull("postgres:16")
    
    # Create and start the container
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
    
    # Wait for container to be ready
    time.sleep(2)  # Give the container a moment to start
    
    # Wait for PostgreSQL to be ready
    is_ready = False
    retry_count = 0
    max_retries = 10
    
    while not is_ready and retry_count < max_retries:
        try:
            # Try to create a test connection
            test_engine = create_engine(TEST_DATABASE_URL)
            # Simply test the connection
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
    
    # Return container info
    container_info = {
        "container": container,
        "db_url": TEST_DATABASE_URL,
        "db_name": POSTGRES_TEST_DB,
        "user": POSTGRES_TEST_USER,
        "password": POSTGRES_TEST_PASSWORD,
        "port": POSTGRES_TEST_PORT
    }
    
    yield container_info
    
    # Cleanup: stop the container
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
    """Creates a new database session for each test function"""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestSessionLocal()
    
    yield session
    
    # Clean up
    session.close()
    transaction.rollback()
    connection.close()
