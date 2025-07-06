import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.session import Base

# Create a test client for FastAPI
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client

# Test database fixtures
@pytest.fixture(scope="module")
def test_db_engine():
    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    yield engine
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

# This fixture can be used later when testing API endpoints that use database
# @pytest.fixture(scope="function")
# def override_get_db(test_db_session):
#     """Override the get_db dependency for testing"""
#     def _get_test_db():
#         try:
#             yield test_db_session
#         finally:
#             pass
#     
#     return _get_test_db
