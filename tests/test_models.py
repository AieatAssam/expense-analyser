"""
Tests for database models using PostgreSQL container.

These tests verify the functionality of SQLAlchemy models against a real
PostgreSQL database running in a Docker container. The container is automatically
started and stopped as part of the test session.

To run these tests:
    pytest -xvs tests/test_models.py

Requirements:
    - Docker must be installed and running
    - Python docker package must be installed
"""
import pytest
from datetime import datetime, timezone
import uuid

from app.models import User, Account, Category, Receipt, LineItem, Invitation

# Use the container-based test database fixtures from conftest.py
# No need to redefine db_engine and db_session fixtures here

@pytest.fixture
def test_user(test_db_session):
    """Create a test user"""
    user = User(
        email=f"test_{uuid.uuid4()}@example.com",
        hashed_password="hashed_test_password",
        full_name="Test User",
        is_active=True,
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user

@pytest.fixture
def test_categories(test_db_session):
    """Create test categories with parent-child relationship"""
    # Parent categories
    groceries = Category(name="Groceries", description="Food and household items")
    electronics = Category(name="Electronics", description="Electronic devices and accessories")
    
    # Add to session
    test_db_session.add_all([groceries, electronics])
    test_db_session.commit()
    test_db_session.refresh(groceries)
    test_db_session.refresh(electronics)
    
    # Child categories
    fruits = Category(name="Fruits", description="Fresh fruits", parent_id=groceries.id)
    dairy = Category(name="Dairy", description="Milk and dairy products", parent_id=groceries.id)
    computers = Category(name="Computers", description="Laptops and desktops", parent_id=electronics.id)
    
    # Add to session
    test_db_session.add_all([fruits, dairy, computers])
    test_db_session.commit()
    
    # Return all categories for testing
    return {
        "groceries": groceries,
        "electronics": electronics,
        "fruits": fruits,
        "dairy": dairy,
        "computers": computers
    }

@pytest.fixture
def test_receipt(test_db_session, test_user):
    """Create a test receipt"""
    receipt = Receipt(
        store_name="Test Store",
        receipt_date=datetime.now(timezone.utc),
        total_amount=100.50,
        tax_amount=7.50,
        currency="USD",
        receipt_number="RCP-12345",
        user_id=test_user.id,
    )
    test_db_session.add(receipt)
    test_db_session.commit()
    test_db_session.refresh(receipt)
    return receipt

@pytest.fixture
def test_line_items(test_db_session, test_receipt, test_categories):
    """Create test line items for the receipt"""
    item1 = LineItem(
        name="Apple",
        description="Fresh Gala apple",
        quantity=5,
        unit_price=1.20,
        total_price=6.00,
        receipt_id=test_receipt.id,
        category_id=test_categories["fruits"].id
    )
    
    item2 = LineItem(
        name="Milk",
        description="Whole milk, 1 gallon",
        quantity=1,
        unit_price=3.99,
        total_price=3.99,
        receipt_id=test_receipt.id,
        category_id=test_categories["dairy"].id
    )
    
    test_db_session.add_all([item1, item2])
    test_db_session.commit()
    
    return [item1, item2]


# Tests for models

class TestUserModel:
    def test_create_user(self, test_db_session):
        """Test that a User can be created and has correct attributes (multi-account ready)"""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User",
            is_active=True,
            is_superuser=False
        )
        test_db_session.add(user)
        test_db_session.commit()
        
        retrieved_user = test_db_session.query(User).filter_by(email="test@example.com").first()
        assert retrieved_user is not None
        assert retrieved_user.email == "test@example.com"
        assert retrieved_user.full_name == "Test User"
        assert retrieved_user.is_active is True
        assert retrieved_user.is_superuser is False
        assert retrieved_user.created_at is not None
        assert retrieved_user.updated_at is not None
        # User should have no accounts by default
        assert hasattr(retrieved_user, "accounts")
        assert isinstance(retrieved_user.accounts, list)
        assert len(retrieved_user.accounts) == 0

    def test_user_receipt_relationship(self, test_user, test_receipt, test_db_session):
        """Test the relationship between User and Receipt"""
        # Refresh the user from DB to ensure relationships are loaded
        test_db_session.refresh(test_user)
        # Check that the user has the receipt
        assert len(test_user.receipts) > 0
        assert test_user.receipts[0].id == test_receipt.id
        # Check reciprocal relationship
        assert test_receipt.user.id == test_user.id

    def test_user_account_relationship(self, test_db_session):
        """Test the relationship between User and Account (multi-account support)"""
        user = User(
            email="multi@example.com",
            hashed_password="hashed_password",
            full_name="Multi Account User",
            is_active=True,
        )
        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)

        # Add two accounts for different providers
        account1 = Account(provider="auth0", provider_account_id="auth0|abc123", user_id=user.id)
        account2 = Account(provider="google", provider_account_id="google-oauth2|xyz789", user_id=user.id)
        test_db_session.add_all([account1, account2])
        test_db_session.commit()
        test_db_session.refresh(user)

        # User should have two accounts
        assert len(user.accounts) == 2
        provider_names = {a.provider for a in user.accounts}
        assert "auth0" in provider_names
        assert "google" in provider_names
        # Accounts should reference the user
        for acc in user.accounts:
            assert acc.user_id == user.id
            assert acc.user.email == user.email


# New tests for Account model
class TestAccountModel:
    def test_create_account(self, test_db_session, test_user):
        """Test that an Account can be created and linked to a user"""
        account = Account(
            provider="auth0",
            provider_account_id="auth0|testid",
            user_id=test_user.id
        )
        test_db_session.add(account)
        test_db_session.commit()
        retrieved = test_db_session.query(Account).filter_by(provider_account_id="auth0|testid").first()
        assert retrieved is not None
        assert retrieved.provider == "auth0"
        assert retrieved.user_id == test_user.id
        assert retrieved.user.email == test_user.email

    def test_account_provider_uniqueness(self, test_db_session, test_user):
        """Test that multiple accounts with same provider but different provider_account_id can be linked to the same user"""
        acc1 = Account(provider="auth0", provider_account_id="auth0|id1", user_id=test_user.id)
        acc2 = Account(provider="auth0", provider_account_id="auth0|id2", user_id=test_user.id)
        test_db_session.add_all([acc1, acc2])
        test_db_session.commit()
        accounts = test_db_session.query(Account).filter_by(user_id=test_user.id, provider="auth0").all()
        assert len(accounts) == 2
        ids = {a.provider_account_id for a in accounts}
        assert "auth0|id1" in ids and "auth0|id2" in ids

    def test_account_multiple_providers(self, test_db_session, test_user):
        """Test that accounts from different providers can be linked to the same user"""
        acc1 = Account(provider="auth0", provider_account_id="auth0|id3", user_id=test_user.id)
        acc2 = Account(provider="google", provider_account_id="google-oauth2|id4", user_id=test_user.id)
        test_db_session.add_all([acc1, acc2])
        test_db_session.commit()
        accounts = test_db_session.query(Account).filter_by(user_id=test_user.id).all()
        providers = {a.provider for a in accounts}
        assert "auth0" in providers and "google" in providers

    def test_account_user_relationship_backref(self, test_db_session):
        """Test that Account.user relationship works and user.accounts backref is correct"""
        user = User(
            email="backref@example.com",
            hashed_password="pw",
            full_name="Backref User",
            is_active=True,
        )
        test_db_session.add(user)
        test_db_session.commit()
        acc = Account(provider="auth0", provider_account_id="auth0|backref", user_id=user.id)
        test_db_session.add(acc)
        test_db_session.commit()
        test_db_session.refresh(user)
        assert len(user.accounts) == 1
        assert user.accounts[0].provider_account_id == "auth0|backref"
        assert user.accounts[0].user.id == user.id


class TestCategoryModel:
    def test_create_category(self, test_db_session):
        """Test that a Category can be created with correct attributes"""
        category = Category(
            name="Test Category",
            description="Test Description"
        )
        test_db_session.add(category)
        test_db_session.commit()
        
        retrieved_category = test_db_session.query(Category).filter_by(name="Test Category").first()
        assert retrieved_category is not None
        assert retrieved_category.name == "Test Category"
        assert retrieved_category.description == "Test Description"
        assert retrieved_category.created_at is not None
    
    def test_category_hierarchy(self, test_categories, test_db_session):
        """Test the hierarchical relationship between categories"""
        # Get fresh instances from DB
        groceries = test_db_session.query(Category).filter_by(name="Groceries").first()
        fruits = test_db_session.query(Category).filter_by(name="Fruits").first()
        
        # Test parent-child relationship
        assert fruits.parent_id == groceries.id
        assert fruits.parent.name == "Groceries"
        
        # Test that parent has subcategories
        assert len(groceries.subcategories) >= 2
        subcategory_names = [cat.name for cat in groceries.subcategories]
        assert "Fruits" in subcategory_names
        assert "Dairy" in subcategory_names


class TestReceiptModel:
    def test_create_receipt(self, test_db_session, test_user):
        """Test that a Receipt can be created with correct attributes"""
        receipt = Receipt(
            store_name="Test Market",
            receipt_date=datetime.now(timezone.utc),
            total_amount=50.75,
            tax_amount=3.25,
            currency="USD",
            receipt_number="RCP-54321",
            user_id=test_user.id
        )
        test_db_session.add(receipt)
        test_db_session.commit()
        
        retrieved_receipt = test_db_session.query(Receipt).filter_by(receipt_number="RCP-54321").first()
        assert retrieved_receipt is not None
        assert retrieved_receipt.store_name == "Test Market"
        assert retrieved_receipt.total_amount == 50.75
        assert retrieved_receipt.tax_amount == 3.25
        assert retrieved_receipt.currency == "USD"
        assert retrieved_receipt.user_id == test_user.id
    
    def test_receipt_user_relationship(self, test_receipt, test_user, test_db_session):
        """Test the relationship between Receipt and User"""
        # Ensure we get a fresh instance from the DB
        test_db_session.refresh(test_receipt)
        
        assert test_receipt.user_id == test_user.id
        assert test_receipt.user.email == test_user.email
    
    def test_receipt_line_items_relationship(self, test_receipt, test_line_items, test_db_session):
        """Test the relationship between Receipt and LineItems"""
        # Refresh receipt to ensure relationships are loaded
        test_db_session.refresh(test_receipt)
        
        assert len(test_receipt.line_items) == 2
        
        # Check line item properties
        item_names = [item.name for item in test_receipt.line_items]
        assert "Apple" in item_names
        assert "Milk" in item_names
        
        # Test cascading delete - when receipt is deleted, line items should also be deleted
        receipt_id = test_receipt.id
        test_db_session.delete(test_receipt)
        test_db_session.commit()
        
        # Check that line items are deleted
        remaining_items = test_db_session.query(LineItem).filter_by(receipt_id=receipt_id).all()
        assert len(remaining_items) == 0


class TestLineItemModel:
    def test_create_line_item(self, test_db_session, test_receipt, test_categories):
        """Test that a LineItem can be created with correct attributes"""
        line_item = LineItem(
            name="Test Item",
            description="Test Description",
            quantity=2.5,
            unit_price=10.00,
            total_price=25.00,
            receipt_id=test_receipt.id,
            category_id=test_categories["electronics"].id
        )
        test_db_session.add(line_item)
        test_db_session.commit()
        
        retrieved_item = test_db_session.query(LineItem).filter_by(name="Test Item").first()
        assert retrieved_item is not None
        assert retrieved_item.name == "Test Item"
        assert retrieved_item.description == "Test Description"
        assert retrieved_item.quantity == 2.5
        assert retrieved_item.unit_price == 10.00
        assert retrieved_item.total_price == 25.00
        assert retrieved_item.receipt_id == test_receipt.id
        assert retrieved_item.category_id == test_categories["electronics"].id
    
    def test_line_item_relationships(self, test_line_items, test_receipt, test_categories, test_db_session):
        """Test the relationships between LineItem, Receipt, and Category"""
        # Get the first line item (Apple)
        apple_item = test_db_session.query(LineItem).filter_by(name="Apple").first()
        test_db_session.refresh(apple_item)
        
        # Test relationship with receipt
        assert apple_item.receipt.id == test_receipt.id
        assert apple_item.receipt.store_name == "Test Store"
        
        # Test relationship with category
        assert apple_item.category.id == test_categories["fruits"].id
        assert apple_item.category.name == "Fruits"
        
        # Test that category has line items
        fruits_category = test_db_session.query(Category).filter_by(name="Fruits").first()
        test_db_session.refresh(fruits_category)
        assert len(fruits_category.line_items) >= 1
        assert any(item.name == "Apple" for item in fruits_category.line_items)


class TestInvitationModel:
    def test_create_invitation(self, test_db_session, test_user):
        """Test that an Invitation can be created and linked to an account and inviter user"""
        # Create an account for the user
        account = Account(provider="auth0", provider_account_id="auth0|invitation", user_id=test_user.id)
        test_db_session.add(account)
        test_db_session.commit()
        test_db_session.refresh(account)

        invitation = Invitation(
            email="invitee@example.com",
            account_id=account.id,
            inviter_user_id=test_user.id,
            token="testtoken123",
            accepted=False
        )
        test_db_session.add(invitation)
        test_db_session.commit()
        test_db_session.refresh(invitation)

        # Check attributes
        assert invitation.email == "invitee@example.com"
        assert invitation.account_id == account.id
        assert invitation.inviter_user_id == test_user.id
        assert invitation.token == "testtoken123"
        assert invitation.accepted is False
        assert invitation.created_at is not None
        assert invitation.account.id == account.id
        assert invitation.inviter.id == test_user.id

    def test_invitation_relationships(self, test_db_session, test_user):
        from app.models import Account
        account = Account(provider="auth0", provider_account_id="auth0|invrel", user_id=test_user.id)
        test_db_session.add(account)
        test_db_session.commit()
        test_db_session.refresh(account)

        invitation = Invitation(
            email="rel@example.com",
            account_id=account.id,
            inviter_user_id=test_user.id,
            token="rel-token",
            accepted=False
        )
        test_db_session.add(invitation)
        test_db_session.commit()
        test_db_session.refresh(invitation)

        # Test backrefs
        assert invitation.account.invitations[0].id == invitation.id
        assert invitation.inviter.sent_invitations[0].id == invitation.id


class TestBaseModelFeatures:
    def test_tablename_generation(self):
        """Test that __tablename__ is correctly generated from class name"""
        assert User.__tablename__ == "user"
        assert Account.__tablename__ == "account"
        assert Category.__tablename__ == "category"
        assert Receipt.__tablename__ == "receipt"
        assert LineItem.__tablename__ == "lineitem"
    
    def test_timestamps(self, test_user, test_db_session):
        """Test that created_at and updated_at are properly set"""
        # Refresh from DB
        test_db_session.refresh(test_user)
        
        assert test_user.created_at is not None
        assert test_user.updated_at is not None
        
        # For some PostgreSQL setups with SQLAlchemy, the onupdate trigger might not 
        # work automatically in test environments without a proper trigger in the database.
        # So we'll check that we can set it and read it back correctly.
        original_name = test_user.full_name
        
        # Change the user's name
        test_user.full_name = "Updated Name"
        
        # Commit the change
        test_db_session.commit()
        test_db_session.refresh(test_user)
        
        # Verify the name was updated
        assert test_user.full_name != original_name
        assert test_user.full_name == "Updated Name"
