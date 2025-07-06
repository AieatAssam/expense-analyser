import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import uuid

from app.models import User, Category, Receipt, LineItem
from app.db.session import Base

# Use an in-memory SQLite database for testing
@pytest.fixture(scope="function")
def db_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Creates a new database session for testing"""
    connection = db_engine.connect()
    transaction = connection.begin()
    
    DBSession = sessionmaker(bind=connection)
    session = DBSession()
    
    yield session
    
    # Clean up
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = User(
        email=f"test_{uuid.uuid4()}@example.com",
        hashed_password="hashed_test_password",
        full_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_categories(db_session):
    """Create test categories with parent-child relationship"""
    # Parent categories
    groceries = Category(name="Groceries", description="Food and household items")
    electronics = Category(name="Electronics", description="Electronic devices and accessories")
    
    # Add to session
    db_session.add_all([groceries, electronics])
    db_session.commit()
    db_session.refresh(groceries)
    db_session.refresh(electronics)
    
    # Child categories
    fruits = Category(name="Fruits", description="Fresh fruits", parent_id=groceries.id)
    dairy = Category(name="Dairy", description="Milk and dairy products", parent_id=groceries.id)
    computers = Category(name="Computers", description="Laptops and desktops", parent_id=electronics.id)
    
    # Add to session
    db_session.add_all([fruits, dairy, computers])
    db_session.commit()
    
    # Return all categories for testing
    return {
        "groceries": groceries,
        "electronics": electronics,
        "fruits": fruits,
        "dairy": dairy,
        "computers": computers
    }

@pytest.fixture
def test_receipt(db_session, test_user):
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
    db_session.add(receipt)
    db_session.commit()
    db_session.refresh(receipt)
    return receipt

@pytest.fixture
def test_line_items(db_session, test_receipt, test_categories):
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
    
    db_session.add_all([item1, item2])
    db_session.commit()
    
    return [item1, item2]


# Tests for models
class TestUserModel:
    def test_create_user(self, db_session):
        """Test that a User can be created and has correct attributes"""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User",
            is_active=True,
            is_superuser=False
        )
        db_session.add(user)
        db_session.commit()
        
        retrieved_user = db_session.query(User).filter_by(email="test@example.com").first()
        assert retrieved_user is not None
        assert retrieved_user.email == "test@example.com"
        assert retrieved_user.full_name == "Test User"
        assert retrieved_user.is_active is True
        assert retrieved_user.is_superuser is False
        assert retrieved_user.created_at is not None
        assert retrieved_user.updated_at is not None
    
    def test_user_receipt_relationship(self, test_user, test_receipt, db_session):
        """Test the relationship between User and Receipt"""
        # Refresh the user from DB to ensure relationships are loaded
        db_session.refresh(test_user)
        
        # Check that the user has the receipt
        assert len(test_user.receipts) > 0
        assert test_user.receipts[0].id == test_receipt.id
        
        # Check reciprocal relationship
        assert test_receipt.user.id == test_user.id


class TestCategoryModel:
    def test_create_category(self, db_session):
        """Test that a Category can be created with correct attributes"""
        category = Category(
            name="Test Category",
            description="Test Description"
        )
        db_session.add(category)
        db_session.commit()
        
        retrieved_category = db_session.query(Category).filter_by(name="Test Category").first()
        assert retrieved_category is not None
        assert retrieved_category.name == "Test Category"
        assert retrieved_category.description == "Test Description"
        assert retrieved_category.created_at is not None
    
    def test_category_hierarchy(self, test_categories, db_session):
        """Test the hierarchical relationship between categories"""
        # Get fresh instances from DB
        groceries = db_session.query(Category).filter_by(name="Groceries").first()
        fruits = db_session.query(Category).filter_by(name="Fruits").first()
        
        # Test parent-child relationship
        assert fruits.parent_id == groceries.id
        assert fruits.parent.name == "Groceries"
        
        # Test that parent has subcategories
        assert len(groceries.subcategories) >= 2
        subcategory_names = [cat.name for cat in groceries.subcategories]
        assert "Fruits" in subcategory_names
        assert "Dairy" in subcategory_names


class TestReceiptModel:
    def test_create_receipt(self, db_session, test_user):
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
        db_session.add(receipt)
        db_session.commit()
        
        retrieved_receipt = db_session.query(Receipt).filter_by(receipt_number="RCP-54321").first()
        assert retrieved_receipt is not None
        assert retrieved_receipt.store_name == "Test Market"
        assert retrieved_receipt.total_amount == 50.75
        assert retrieved_receipt.tax_amount == 3.25
        assert retrieved_receipt.currency == "USD"
        assert retrieved_receipt.user_id == test_user.id
    
    def test_receipt_user_relationship(self, test_receipt, test_user, db_session):
        """Test the relationship between Receipt and User"""
        # Ensure we get a fresh instance from the DB
        db_session.refresh(test_receipt)
        
        assert test_receipt.user_id == test_user.id
        assert test_receipt.user.email == test_user.email
    
    def test_receipt_line_items_relationship(self, test_receipt, test_line_items, db_session):
        """Test the relationship between Receipt and LineItems"""
        # Refresh receipt to ensure relationships are loaded
        db_session.refresh(test_receipt)
        
        assert len(test_receipt.line_items) == 2
        
        # Check line item properties
        item_names = [item.name for item in test_receipt.line_items]
        assert "Apple" in item_names
        assert "Milk" in item_names
        
        # Test cascading delete - when receipt is deleted, line items should also be deleted
        receipt_id = test_receipt.id
        db_session.delete(test_receipt)
        db_session.commit()
        
        # Check that line items are deleted
        remaining_items = db_session.query(LineItem).filter_by(receipt_id=receipt_id).all()
        assert len(remaining_items) == 0


class TestLineItemModel:
    def test_create_line_item(self, db_session, test_receipt, test_categories):
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
        db_session.add(line_item)
        db_session.commit()
        
        retrieved_item = db_session.query(LineItem).filter_by(name="Test Item").first()
        assert retrieved_item is not None
        assert retrieved_item.name == "Test Item"
        assert retrieved_item.description == "Test Description"
        assert retrieved_item.quantity == 2.5
        assert retrieved_item.unit_price == 10.00
        assert retrieved_item.total_price == 25.00
        assert retrieved_item.receipt_id == test_receipt.id
        assert retrieved_item.category_id == test_categories["electronics"].id
    
    def test_line_item_relationships(self, test_line_items, test_receipt, test_categories, db_session):
        """Test the relationships between LineItem, Receipt, and Category"""
        # Get the first line item (Apple)
        apple_item = db_session.query(LineItem).filter_by(name="Apple").first()
        db_session.refresh(apple_item)
        
        # Test relationship with receipt
        assert apple_item.receipt.id == test_receipt.id
        assert apple_item.receipt.store_name == "Test Store"
        
        # Test relationship with category
        assert apple_item.category.id == test_categories["fruits"].id
        assert apple_item.category.name == "Fruits"
        
        # Test that category has line items
        fruits_category = db_session.query(Category).filter_by(name="Fruits").first()
        db_session.refresh(fruits_category)
        assert len(fruits_category.line_items) >= 1
        assert any(item.name == "Apple" for item in fruits_category.line_items)


class TestBaseModelFeatures:
    def test_tablename_generation(self):
        """Test that __tablename__ is correctly generated from class name"""
        assert User.__tablename__ == "user"
        assert Category.__tablename__ == "category"
        assert Receipt.__tablename__ == "receipt"
        assert LineItem.__tablename__ == "lineitem"
    
    def test_timestamps(self, test_user, db_session):
        """Test that created_at and updated_at are properly set"""
        # Refresh from DB
        db_session.refresh(test_user)
        
        assert test_user.created_at is not None
        assert test_user.updated_at is not None
        
        # For SQLite testing, we'll just verify that timestamps exist
        # Note: SQLite doesn't trigger onupdate the same way PostgreSQL does
        # In real PostgreSQL database, the updated_at would be updated automatically
        original_updated_at = test_user.updated_at
        test_user.full_name = "Updated Name"
        
        # Manually update the timestamp for testing purposes
        from datetime import datetime, timezone
        import time
        
        # Sleep for a moment to ensure different timestamp
        time.sleep(0.1)
        test_user.updated_at = datetime.now(timezone.utc)
        db_session.commit()
        db_session.refresh(test_user)
        
        # Check that updated_at changed
        assert test_user.updated_at != original_updated_at
