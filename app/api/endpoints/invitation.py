from app.models.user import User
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.invitation import InvitationCreate, InvitationOut, InvitationAccept
from app.core.invitation import create_invitation, get_invitation_by_token, accept_invitation
from app.db.session import get_db
from app.models.account import Account

from app.core.auth import get_current_user

router = APIRouter()

@router.post("/invite", response_model=InvitationOut)
def invite_user(invite: InvitationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    account = db.query(Account).filter(Account.id == invite.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.user_id != current_user.id and not getattr(current_user, "is_superuser", False):
        raise HTTPException(status_code=403, detail="Not authorized to invite users to this account")

    invitation = create_invitation(db, invite.email, invite.account_id, current_user.id)
    return invitation

@router.post("/accept-invitation", response_model=InvitationOut)
def accept_invite(data: InvitationAccept, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    invitation = accept_invitation(db, data.token, current_user)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invalid or already accepted invitation token")
    return invitation

@router.get("/invitation/{token}", response_model=InvitationOut)
def get_invite(token: str, db: Session = Depends(get_db)):
    invitation = get_invitation_by_token(db, token)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    return invitation
