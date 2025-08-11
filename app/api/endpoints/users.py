from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.account import Account

router = APIRouter()

def _serialize_account(acc: Account) -> dict:
    # Frontend expects id as string and a name field
    return {
        "id": str(acc.id),
        "name": getattr(acc, "name", None) or "Primary Account",
    }

@router.get("/profile", tags=["users"])
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return the current authenticated user's profile (user + accounts)."""
    # Load accounts for the user
    accounts = db.query(Account).filter(Account.user_id == current_user.id).all()
    accounts_payload = [_serialize_account(a) for a in accounts]
    current_account = accounts_payload[0] if accounts_payload else {"id": "0", "name": "Primary Account"}

    return {
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "name": current_user.full_name or None,
            "picture": None,
        },
        "accounts": accounts_payload,
        "currentAccount": current_account,
    }

@router.get("/accounts", tags=["users"])
def get_accounts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    accounts = db.query(Account).filter(Account.user_id == current_user.id).all()
    return [_serialize_account(a) for a in accounts]

@router.post("/switch-account", tags=["users"])
def switch_account(current_user: User = Depends(get_current_user)):
    # No server-side persisted state for "current account" yet; acknowledge success.
    return {"success": True}
