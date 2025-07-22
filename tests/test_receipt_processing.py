import pytest
from unittest.mock import MagicMock
from datetime import datetime

from app.core.receipt_processor import ReceiptProcessingOrchestrator, ProcessingStatus
from app.core.processing_status import ProcessingStatusTracker, ProcessingEventType
from app.models.receipt import Receipt
from app.models.category import Category


@pytest.fixture
def mock_llm_client():
    """Mock LLM client that returns a successful response"""
    mock_client = MagicMock()
    mock_client.provider_name = "test-provider"
    mock_client.send.return_value = {
        "response": {
            "store_name": "Test Store",
            "date": "2025-07-22",
            "total_amount": 42.50,
            "line_items": [
                {"name": "Item 1", "category": "Groceries", "amount": 12.50},
                {"name": "Item 2", "category": "Electronics", "amount": 30.00}
            ]
        }
    }
    return mock_client


@pytest.fixture
def mock_validator():
    """Mock validator that returns successful validation"""
    mock_val = MagicMock()
    mock_val.validate.return_value = (True, [])
    mock_val.fallback_parse.return_value = {
        "store_name": "Fallback Store",
        "date": "2025-07-22",
        "total_amount": 10.00,
        "line_items": [{"name": "Fallback Item", "category": "Other", "amount": 10.00}]
    }
    return mock_val


@pytest.fixture
def test_receipt(test_db_session):
    """Create a test receipt"""
    # Create test user first
    from app.models.user import User
    user = User(
        email="test@example.com",
        hashed_password="test-password-hash",
        full_name="Test User"
    )
    test_db_session.add(user)
    test_db_session.commit()
    
    # Create test receipt
    receipt = Receipt(
        user_id=user.id,
        store_name="Unknown Store",
        receipt_date=datetime.now(),
        total_amount=0.0,
        processing_status=ProcessingStatus.UPLOADED,
        image_data=b'test_image_data',
        image_format='jpg'
    )
    test_db_session.add(receipt)
    test_db_session.commit()
    test_db_session.refresh(receipt)
    return receipt


def test_receipt_processor_init(test_db_session):
    """Test processor initialization"""
    processor = ReceiptProcessingOrchestrator(test_db_session)
    assert processor.db == test_db_session
    assert processor.llm_client is not None
    assert processor.validator is not None
    assert processor.status_tracker is not None
    assert processor.receipt_type == "default"


def test_receipt_processing_success(test_db_session, test_receipt, mock_llm_client, mock_validator):
    """Test successful receipt processing flow"""
    processor = ReceiptProcessingOrchestrator(
        test_db_session,
        llm_client=mock_llm_client,
        validator=mock_validator
    )
    
    # Process receipt
    updated_receipt = processor.process_receipt(test_receipt.id)
    
    # Verify receipt was updated
    assert updated_receipt.processing_status == ProcessingStatus.COMPLETED
    assert updated_receipt.store_name == "Test Store"
    assert updated_receipt.total_amount == 42.50
    
    # Verify line items were created
    test_db_session.refresh(updated_receipt)
    assert len(updated_receipt.line_items) == 2
    
    # Verify event tracking
    status_tracker = ProcessingStatusTracker(test_db_session)
    events = status_tracker.get_processing_history(test_receipt.id)
    assert len(events) > 0
    
    # Verify categories were created
    categories = test_db_session.query(Category).all()
    category_names = [c.name for c in categories]
    assert "Groceries" in category_names
    assert "Electronics" in category_names


def test_receipt_processing_validation_failure(test_db_session, test_receipt, mock_llm_client):
    """Test receipt processing with validation failure"""
    mock_validator = MagicMock()
    mock_validator.validate.return_value = (False, ["Line items total doesn't match receipt total"])
    
    processor = ReceiptProcessingOrchestrator(
        test_db_session,
        llm_client=mock_llm_client,
        validator=mock_validator
    )
    
    # Process receipt
    updated_receipt = processor.process_receipt(test_receipt.id)
    
    # Verify receipt was marked for manual review
    assert updated_receipt.processing_status == ProcessingStatus.MANUAL_REVIEW
    
    # Verify event tracking includes warning
    status_tracker = ProcessingStatusTracker(test_db_session)
    events = status_tracker.get_processing_history(test_receipt.id)
    has_warning = any(e.event_type == ProcessingEventType.WARNING for e in events)
    assert has_warning


def test_receipt_processing_llm_failure(test_db_session, test_receipt):
    """Test receipt processing with LLM failure"""
    # Mock LLM client that raises an exception
    mock_error_client = MagicMock()
    mock_error_client.provider_name = "test-provider"
    mock_error_client.send.side_effect = Exception("LLM service unavailable")
    
    processor = ReceiptProcessingOrchestrator(
        test_db_session,
        llm_client=mock_error_client
    )
    
    # Process receipt should handle the exception
    processor.process_receipt(test_receipt.id)
    
    # Verify receipt was marked as error or failed
    test_db_session.refresh(test_receipt)
    assert test_receipt.processing_status in [ProcessingStatus.ERROR, ProcessingStatus.FAILED]
    
    # Verify error was tracked
    status_tracker = ProcessingStatusTracker(test_db_session)
    events = status_tracker.get_processing_history(test_receipt.id)
    has_error = any(e.event_type == ProcessingEventType.ERROR for e in events)
    assert has_error


def test_receipt_processing_fallback_parsing(test_db_session, test_receipt, mock_validator):
    """Test receipt processing with fallback parsing"""
    # Mock LLM client that returns an unparseable string
    mock_client = MagicMock()
    mock_client.provider_name = "test-provider"
    mock_client.send.return_value = {"response": "This is not valid JSON"}
    
    processor = ReceiptProcessingOrchestrator(
        test_db_session,
        llm_client=mock_client,
        validator=mock_validator
    )
    
    # Process receipt
    updated_receipt = processor.process_receipt(test_receipt.id)
    
    # Verify fallback parsing was used
    assert updated_receipt.store_name == "Fallback Store"
    assert updated_receipt.total_amount == 10.00
    
    # Verify line items were created from fallback
    test_db_session.refresh(updated_receipt)
    assert len(updated_receipt.line_items) == 1
    assert updated_receipt.line_items[0].name == "Fallback Item"
