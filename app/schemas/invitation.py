from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class InvitationBase(BaseModel):
    email: EmailStr
    account_id: int

class InvitationCreate(InvitationBase):
    pass

class InvitationAccept(BaseModel):
    token: str

class InvitationOut(InvitationBase):
    id: int
    inviter_user_id: int
    accepted: bool
    created_at: datetime
    accepted_at: Optional[datetime]
    token: str

    class Config:
        orm_mode = True
