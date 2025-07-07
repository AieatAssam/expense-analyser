from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, func
from sqlalchemy.orm import relationship
from app.models.base import Base

class Invitation(Base):
    __tablename__ = "invitations"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("account.id"), nullable=False)
    inviter_user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    token = Column(String, nullable=False, unique=True, index=True)
    accepted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    accepted_at = Column(DateTime(timezone=True), nullable=True)

    account = relationship("Account", back_populates="invitations")
    inviter = relationship("User", back_populates="sent_invitations")
