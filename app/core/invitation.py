import secrets
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.invitation import Invitation
from app.models.user import User
from app.models.account import Account

INVITATION_TOKEN_BYTES = 32

def create_invitation(db: Session, email: str, account_id: int, inviter_user_id: int) -> Invitation:
    token = secrets.token_urlsafe(INVITATION_TOKEN_BYTES)
    invitation = Invitation(
        email=email,
        account_id=account_id,
        inviter_user_id=inviter_user_id,
        token=token,
        accepted=False
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation

def get_invitation_by_token(db: Session, token: str) -> Invitation:
    return db.query(Invitation).filter(Invitation.token == token).first()

def accept_invitation(db: Session, token: str, user: User) -> Invitation:
    invitation = get_invitation_by_token(db, token)
    if not invitation or invitation.accepted:
        return None
    # Link user to account if not already linked
    account = db.query(Account).filter(Account.id == invitation.account_id).first()
    if account and account.user_id != user.id:
        account.user_id = user.id
        db.add(account)
    invitation.accepted = True
    invitation.accepted_at = datetime.utcnow()
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation
