
import os
os.environ["AUTH0_DOMAIN"] = "test-auth0-domain.auth0.com"
os.environ["AUTH0_API_AUDIENCE"] = "test-api-audience"
os.environ["AUTH0_CLIENT_ID"] = "test-client-id"
os.environ["AUTH0_CLIENT_SECRET"] = "test-client-secret"
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
    
    # Stop and remove any existing test container
    try:
        existing_container = client.containers.get("expense_test_db")
        print("Stopping existing PostgreSQL test container...")
        existing_container.stop()
        existing_container.remove()
        print("Existing container removed")
    except docker.errors.NotFound:
        pass  # Container doesn't exist, which is fine
    except Exception as e:
        print(f"Error cleaning up existing container: {e}")
    
    # Clean up any processes using the test port
    import subprocess
    try:
        result = subprocess.run(['lsof', '-ti', f':{POSTGRES_TEST_PORT}'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    subprocess.run(['kill', '-9', pid], check=True)
                    print(f"Killed process {pid} using port {POSTGRES_TEST_PORT}")
                except subprocess.CalledProcessError:
                    pass  # Process might have already died
    except FileNotFoundError:
        pass  # lsof not available on this system
    
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
    try:
        container.stop()
        container.remove()
        print("PostgreSQL test container stopped and removed")
    except Exception as e:
        print(f"Error stopping container: {e}")
        # Try to force remove
        try:
            container.remove(force=True)
        except Exception:
            pass

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

@pytest.fixture
def sample_receipts(test_db_session):
    """Create sample receipts for testing"""
    from datetime import datetime, timedelta
    from app.models.user import User
    from app.models.receipt import Receipt
    from app.models.line_item import LineItem
    from app.models.category import Category
    
    # Create a test user
    test_user = User(id=1, email="test@example.com", hashed_password="fake_hash", is_active=True)
    test_db_session.add(test_user)
    test_db_session.commit()
    
    # Create categories
    grocery_cat = Category(name="Groceries", description="Food and household items")
    gas_cat = Category(name="Gas", description="Fuel expenses")
    test_db_session.add_all([grocery_cat, gas_cat])
    test_db_session.commit()
    
    # Create receipts
    receipts = []
    base_date = datetime(2023, 6, 1)
    
    for i in range(5):
        receipt = Receipt(
            store_name=f"Store {i+1}",
            receipt_date=base_date + timedelta(days=i*7),
            total_amount=100.0 + (i * 25),
            tax_amount=10.0 + (i * 2.5),
            currency="USD",
            user_id=test_user.id,
            processing_status="completed",
            is_verified=True
        )
        receipts.append(receipt)
        test_db_session.add(receipt)
    
    test_db_session.commit()
    
    # Create line items
    for i, receipt in enumerate(receipts):
        # Add grocery items
        grocery_item = LineItem(
            name=f"Grocery Item {i+1}",
            quantity=1.0,
            unit_price=50.0 + (i * 10),
            total_price=50.0 + (i * 10),
            receipt_id=receipt.id,
            category_id=grocery_cat.id
        )
        
        # Add gas items for some receipts
        if i % 2 == 0:
            gas_item = LineItem(
                name=f"Gas {i+1}",
                quantity=1.0,
                unit_price=40.0 + (i * 15),
                total_price=40.0 + (i * 15),
                receipt_id=receipt.id,
                category_id=gas_cat.id
            )
            test_db_session.add(gas_item)
        
        test_db_session.add(grocery_item)
    
    test_db_session.commit()
    return receipts, [grocery_cat, gas_cat]
