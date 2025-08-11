from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import threading

from app.core.config import settings

# Create database engine
engine = create_engine(settings.DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

_init_lock = threading.Lock()
_initialized = False

def ensure_db_initialized():
    """Create all tables once per process. Safe to call multiple times."""
    global _initialized
    if _initialized:
        return
    with _init_lock:
        if _initialized:
            return
        # Local import to avoid circulars during module import time
        from app.models import user as _user  # noqa: F401
        from app.models import account as _account  # noqa: F401
        from app.models import invitation as _invitation  # noqa: F401
        try:
            Base.metadata.create_all(bind=engine)
        finally:
            _initialized = True

# Dependency to get DB session
def get_db():
    # Ensure tables exist before using the session (idempotent)
    try:
        ensure_db_initialized()
    except Exception:
        # Best-effort; avoid blocking requests if init races
        pass
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
