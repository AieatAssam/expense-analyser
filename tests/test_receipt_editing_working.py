import pytest
from unittest.mock import MagicMock
from datetime import date, datetime
from fastapi import HTTPException

from app.models.receipt import Receipt
from app.models.line_item import LineItem
from app.models.category import Category
from app.models.user import User
from app.schemas.receipt_editing import (
    ReceiptEditRequest, 
    BulkEditRequest
)


@pytest.fixture
def mock_current_user():
    """Create mock current user for testing"""
    user = MagicMock()
    user.id = 1
    user.email = "test@example.com"
    return user


@pytest.fixture
def test_user_with_receipt(test_db_session):
    """Create test user with receipt for testing"""
    # Create test user
    user = User(
        email="test@example.com",
        hashed_password="hashed_password_here",
        full_name="Test User"
    )
    test_db_session.add(user)
    test_db_session.commit()
    
    # Create categories (without user_id since they're global)
    cat1 = Category(name="Groceries", description="Food items")
    cat2 = Category(name="Electronics", description="Electronic devices")
    test_db_session.add_all([cat1, cat2])
    test_db_session.commit()
    
    # Create receipt
    receipt = Receipt(
        user_id=user.id,
        store_name="Test Store",
        receipt_date=datetime(2025, 7, 26),
        total_amount=15.50,
        currency="USD",
        processing_status="processed",
        is_verified=False
    )
    test_db_session.add(receipt)
    test_db_session.commit()
    
    # Create line items
    item1 = LineItem(
        receipt_id=receipt.id,
        name="Milk",
        description="Fresh milk",
        quantity=1.0,
        unit_price=3.50,
        total_price=3.50,
        category_id=cat1.id
    )
    
    item2 = LineItem(
        receipt_id=receipt.id,
        name="Bread",
        description="Whole wheat bread",
        quantity=1.0,
        unit_price=4.00,
        total_price=4.00,
        category_id=cat1.id
    )
    
    test_db_session.add_all([item1, item2])
    test_db_session.commit()
    
    return receipt, user, [item1, item2], [cat1, cat2]


class TestReceiptEditingEndpoints:
    """Test receipt editing API endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_receipt_for_editing_success(self, test_db_session, test_user_with_receipt, mock_current_user):
        """Test getting receipt details for editing"""
        receipt, user, items, categories = test_user_with_receipt
        mock_current_user.id = user.id
        
        from app.api.endpoints.receipt_editing import get_receipt_for_editing
        
        # Call the endpoint function directly
        response = await get_receipt_for_editing(receipt.id, test_db_session, mock_current_user)
        
        assert response.id == receipt.id
        assert response.store_name == "Test Store"
        assert response.total_amount == 15.50
        assert len(response.line_items) == 2
        assert response.line_items[0].name == "Milk"
    
    @pytest.mark.asyncio
    async def test_get_receipt_for_editing_not_found(self, test_db_session, mock_current_user):
        """Test getting non-existent receipt"""
        from app.api.endpoints.receipt_editing import get_receipt_for_editing
        
        with pytest.raises(HTTPException) as exc_info:
            await get_receipt_for_editing(999, test_db_session, mock_current_user)
        
        assert exc_info.value.status_code == 404
        assert "Receipt not found" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_update_receipt_basic_fields(self, test_db_session, test_user_with_receipt, mock_current_user):
        """Test updating basic receipt fields"""
        receipt, user, items, categories = test_user_with_receipt
        mock_current_user.id = user.id
        
        from app.api.endpoints.receipt_editing import update_receipt
        
        edit_request = ReceiptEditRequest(
            store_name="Updated Store Name",
            receipt_date=date(2025, 7, 27),
            total_amount=20.00,
            currency="EUR",
            is_verified=True,
            verification_notes="Manually verified"
        )
        
        response = await update_receipt(receipt.id, edit_request, test_db_session, mock_current_user)
        
        assert response.success is True
        
        # Verify changes in database
        updated_receipt = test_db_session.query(Receipt).filter_by(id=receipt.id).first()
        assert updated_receipt.store_name == "Updated Store Name"
        assert updated_receipt.total_amount == 20.00
        assert updated_receipt.currency == "EUR"
        assert updated_receipt.is_verified is True
        assert updated_receipt.verification_notes == "Manually verified"
    
    @pytest.mark.asyncio
    async def test_bulk_approve_receipts(self, test_db_session, test_user_with_receipt, mock_current_user):
        """Test bulk approval of receipts"""
        receipt, user, items, categories = test_user_with_receipt
        mock_current_user.id = user.id
        
        from app.api.endpoints.receipt_editing import bulk_edit_receipts
        
        bulk_request = BulkEditRequest(
            receipt_ids=[receipt.id],
            operation="approve"
        )
        
        response = await bulk_edit_receipts(bulk_request, test_db_session, mock_current_user)
        
        assert response.success is True
        assert response.processed_count == 1
        
        # Verify receipt was approved
        updated_receipt = test_db_session.query(Receipt).filter_by(id=receipt.id).first()
        assert updated_receipt.is_verified is True
        assert updated_receipt.processing_status == "processed"


def test_receipt_validation_basic(test_db_session):
    """Test validation functionality with basic check"""
    from app.core.receipt_validation import ReceiptAccuracyValidator
    
    validator = ReceiptAccuracyValidator(test_db_session)
    
    # Test that the validator was created successfully
    assert validator is not None
    assert validator.db is test_db_session
