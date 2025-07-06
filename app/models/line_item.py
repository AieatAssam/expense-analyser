from sqlalchemy import Column, String, Float, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

class LineItem(BaseModel):
    """
    LineItem model for storing individual items from receipts
    """
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    quantity = Column(Float, default=1.0, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    
    # Foreign keys
    receipt_id = Column(Integer, ForeignKey("receipt.id"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("category.id"), nullable=True, index=True)
    
    # Relationships
    receipt = relationship("Receipt", back_populates="line_items")
    category = relationship("Category", back_populates="line_items")
    
    def __repr__(self):
        return f"<LineItem {self.name} ${self.total_price}>"
