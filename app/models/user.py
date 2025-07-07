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

    # Remove single auth0_user_id, support multiple accounts via Account model

    # Relationships
    receipts = relationship("Receipt", back_populates="user", cascade="all, delete-orphan")
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    sent_invitations = relationship("Invitation", back_populates="inviter", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"
