from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

class Category(BaseModel):
    """
    Categories model for item categorization with hierarchical structure
    """
    name = Column(String(100), nullable=False)
    description = Column(String(255))
    
    # Self-referential relationship for hierarchical categories
    parent_id = Column(Integer, ForeignKey("category.id"), nullable=True, index=True)
    parent = relationship("Category", remote_side="Category.id", backref="subcategories")
    
    # Relationships
    line_items = relationship("LineItem", back_populates="category")
    
    def __repr__(self):
        return f"<Category {self.name}>"
