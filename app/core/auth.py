import os
import requests
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.account import Account


AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "your-auth0-domain")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID", "your-client-id")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET", "your-client-secret")
API_AUDIENCE = os.getenv("AUTH0_API_AUDIENCE", "your-api-audience")
ALGORITHMS = ["RS256"]

http_bearer = HTTPBearer()

def get_jwks():
    """Fetch JWKS from Auth0 well-known endpoint"""
    try:
        jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
        response = requests.get(jwks_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise Exception(f"Failed to fetch JWKS from Auth0: {e}")

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    db: Session = Depends(get_db),
) -> User:
    import logging
    logger = logging.getLogger("auth.security")
    token = credentials.credentials
    logger.info("Auth event: Received token for validation")
    logger.debug(f"Token: {token}")
    try:
        # Decode header to get kid
        unverified_header = jwt.get_unverified_header(token)
        logger.debug(f"JWT header: {unverified_header}")
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
        logger.debug(f"RSA key used for JWT validation: {rsa_key}")
        if not rsa_key:
            logger.error("Security incident: No RSA key found for JWT kid")
            raise HTTPException(status_code=401, detail="Invalid token header")
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=ALGORITHMS,
            audience=API_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/",
        )
        logger.info(f"Auth event: JWT validated successfully for subject {payload.get('sub')}")
        logger.debug(f"JWT payload: {payload}")
        sub = payload.get("sub")
        email = payload.get("email")
        if not sub or not email:
            logger.error("Security incident: sub or email missing in JWT payload")
            raise HTTPException(status_code=401, detail="Invalid token payload")
        # Check if user exists
        account = db.query(Account).filter(Account.provider=="auth0", Account.provider_account_id==sub).first()
        logger.info(f"Auth event: Account lookup for sub {sub} result: {bool(account)}")
        logger.debug(f"Account object: {account}")
        if account:
            user = db.query(User).filter(User.id==account.user_id).first()
            logger.info(f"Auth event: User lookup for account {account.id} result: {bool(user)}")
            logger.debug(f"User object: {user}")
            if not user:
                logger.error("Security incident: User not found for account")
                raise HTTPException(status_code=401, detail="User not found")
            logger.info(f"Auth event: Authenticated user {user.email}")
            return user
        # If no users exist, auto-create first user
        user_count = db.query(User).count()
        logger.info(f"Auth event: User count in DB: {user_count}")
        if user_count == 0:
            user = User(email=email, hashed_password="", is_active=True, is_superuser=True)
            db.add(user)
            db.commit()
            db.refresh(user)
            account = Account(provider="auth0", provider_account_id=sub, user_id=user.id)
            db.add(account)
            db.commit()
            db.refresh(account)
            logger.info(f"Auth event: Auto-created first user {user.email} and account {account.id}")
            return user
        # Otherwise, not authorized
        logger.warning(f"Security incident: Account {sub} not linked. Invitation required.")
        raise HTTPException(status_code=403, detail="Account not linked. Ask admin for invitation.")
    except JWTError as e:
        logger.error(f"Security incident: JWTError during token validation: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
