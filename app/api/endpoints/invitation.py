from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.invitation import InvitationCreate, InvitationOut, InvitationAccept
from app.core.invitation import create_invitation, get_invitation_by_token, accept_invitation
from app.db.session import get_db
from app.models.user import User
from app.models.invitation import Invitation
# from app.core.auth import get_current_user  # Implement this for real auth

def get_current_user():
    # Dummy user for now, replace with real Auth0 integration
    return User(id=1, email="dummy@example.com", hashed_password="", is_active=True, is_superuser=False)

router = APIRouter()

@router.post("/invite", response_model=InvitationOut)
def invite_user(invite: InvitationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # TODO: Add authorization checks (current_user must be allowed to invite to this account)
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
