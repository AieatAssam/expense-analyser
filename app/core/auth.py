import os
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.account import Account


AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "your-auth0-domain")
API_AUDIENCE = os.getenv("AUTH0_API_AUDIENCE", "your-api-audience")
ALGORITHMS = ["RS256"]

# In production, fetch JWKS from Auth0. For now, use a placeholder.
AUTH0_JWKS = os.getenv("AUTH0_JWKS", None)

http_bearer = HTTPBearer()

def get_jwks():
    # TODO: Fetch JWKS from Auth0 and cache it
    # For now, raise if not set
    if not AUTH0_JWKS:
        raise Exception("Auth0 JWKS not configured")
    import json
    return json.loads(AUTH0_JWKS)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    db: Session = Depends(get_db),
) -> User:
    import logging
    token = credentials.credentials
    logging.warning(f"[DEBUG] get_current_user: token={token}")
    try:
        # Decode header to get kid
        unverified_header = jwt.get_unverified_header(token)
        logging.warning(f"[DEBUG] get_current_user: unverified_header={unverified_header}")
        jwks = get_jwks()
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }
        logging.warning(f"[DEBUG] get_current_user: rsa_key={rsa_key}")
        if not rsa_key:
            logging.warning("[DEBUG] get_current_user: No RSA key found for kid")
            raise HTTPException(status_code=401, detail="Invalid token header")
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=ALGORITHMS,
            audience=API_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/",
        )
        logging.warning(f"[DEBUG] get_current_user: payload={payload}")
        sub = payload.get("sub")
        email = payload.get("email")
        if not sub or not email:
            logging.warning("[DEBUG] get_current_user: sub or email missing in payload")
            raise HTTPException(status_code=401, detail="Invalid token payload")
        # Check if user exists
        account = db.query(Account).filter(Account.provider=="auth0", Account.provider_account_id==sub).first()
        logging.warning(f"[DEBUG] get_current_user: account={account}")
        if account:
            user = db.query(User).filter(User.id==account.user_id).first()
            logging.warning(f"[DEBUG] get_current_user: user={user}")
            if not user:
                logging.warning("[DEBUG] get_current_user: User not found for account")
                raise HTTPException(status_code=401, detail="User not found")
            return user
        # If no users exist, auto-create first user
        user_count = db.query(User).count()
        logging.warning(f"[DEBUG] get_current_user: user_count={user_count}")
        if user_count == 0:
            user = User(email=email, hashed_password="", is_active=True, is_superuser=True)
            db.add(user)
            db.commit()
            db.refresh(user)
            account = Account(provider="auth0", provider_account_id=sub, user_id=user.id)
            db.add(account)
            db.commit()
            db.refresh(account)
            logging.warning(f"[DEBUG] get_current_user: auto-created user={user}, account={account}")
            return user
        # Otherwise, not authorized
        logging.warning("[DEBUG] get_current_user: Account not linked. Ask admin for invitation.")
        raise HTTPException(status_code=403, detail="Account not linked. Ask admin for invitation.")
    except JWTError as e:
        logging.warning(f"[DEBUG] get_current_user: JWTError: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
