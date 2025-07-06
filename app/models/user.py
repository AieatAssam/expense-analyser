from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

class User(BaseModel):
    """
    User model for authentication and user management
    """
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    auth0_user_id = Column(String(128), unique=True, index=True, nullable=True, doc="Auth0 user ID")

    # Relationships
    receipts = relationship("Receipt", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"
