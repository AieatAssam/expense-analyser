from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

class Account(BaseModel):
    """
    Account model for linking Auth0 identities to users (multi-provider support)
    """
    provider = Column(String(50), nullable=False, index=True, doc="Auth provider name, e.g. 'auth0', 'google', etc.")
    provider_account_id = Column(String(128), nullable=False, index=True, doc="Provider-specific account/user id")
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="accounts")

    def __repr__(self):
        return f"<Account {self.provider}:{self.provider_account_id} for user {self.user_id}>"
