from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Boolean, Text, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel

class Receipt(BaseModel):
    """
    Receipt model for storing receipt metadata and relationships
    """
    store_name = Column(String(255), nullable=False, index=True)
    receipt_date = Column(DateTime(timezone=True), default=func.now(), nullable=False, index=True)
    total_amount = Column(Float, nullable=False)
    tax_amount = Column(Float, nullable=True)
    currency = Column(String(3), default="USD", nullable=False)
    receipt_number = Column(String(100), nullable=True)
    
    # Processing metadata
    image_path = Column(String(255), nullable=True)
    raw_text = Column(Text, nullable=True)
    processing_status = Column(String(50), default="pending", nullable=False)
    is_verified = Column(Boolean, default=False)
    verification_notes = Column(Text, nullable=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="receipts")
    line_items = relationship("LineItem", back_populates="receipt", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Receipt {self.store_name} {self.receipt_date} ${self.total_amount}>"
