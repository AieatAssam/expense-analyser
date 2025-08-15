from fastapi import FastAPI
from fastapi import WebSocket, WebSocketDisconnect
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
import os

from app.core.config import settings
from app.db.session import Base, engine
# Import models so tables are registered in SQLAlchemy metadata
from app.models import user as user_model  # noqa: F401
from app.models import account as account_model  # noqa: F401
from app.models import invitation as invitation_model  # noqa: F401
from app.core.middleware import RequestLoggingMiddleware
from app.api.api import api_router
from app.core.health import get_health_status
from app.core.websocket_manager import manager
from app.core.auth import get_user_from_token
from app.db.session import SessionLocal

app = FastAPI(
    title="Expense Analyser API",
    description="API for expense receipt analysis and tracking",
    version="0.1.0",
)

# Ensure database tables exist on startup (simple bootstrap for dev/docker)
@app.on_event("startup")
def on_startup_create_tables():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        # Avoid crashing the app on startup; errors will surface in logs
        import logging
        logging.getLogger(__name__).error(f"DB init error: {e}")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Include API routers
app.include_router(api_router, prefix=settings.API_V1_STR)

# Root-level health check endpoints for convenience and compatibility
@app.get("/health", tags=["Health"])
async def root_health_check():
    """
    Root-level health check endpoint for backward compatibility.
    Provides comprehensive health status of all application dependencies.
    """
    health_data = await get_health_status(include_details=False)
    
    # For the root endpoint, always return 200 but include status in response
    # This maintains backward compatibility with existing monitoring
    return health_data


@app.get("/ping", tags=["Health"])
async def root_ping():
    """
    Root-level ping endpoint for basic connectivity testing.
    """
    return {"ping": "pong", "status": "ok"}


@app.get("/ready", tags=["Health"])
async def root_readiness():
    """
    Root-level readiness endpoint for load balancer checks.
    """
    from app.core.health import get_readiness_status
    return await get_readiness_status()


@app.get("/live", tags=["Health"])
async def root_liveness():
    """
    Root-level liveness endpoint for container orchestration.
    """
    from app.core.health import get_liveness_status
    return await get_liveness_status()

# Mount static files for assets
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.isdir(static_dir):
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    
    # Mount the nested static directory for React build assets
    # React builds create a structure like: static/static/css/ and static/static/js/
    nested_static_dir = os.path.join(static_dir, "static")
    if os.path.isdir(nested_static_dir):
        app.mount("/static", StaticFiles(directory=nested_static_dir), name="static")
    
    # Serve the index.html at the root
    @app.get("/", include_in_schema=False)
    async def read_root():
        return FileResponse(os.path.join(static_dir, "index.html"))
    
    # Catch-all route for SPA routing - serve index.html for any unmatched routes
    # This ensures React Router can handle client-side routing
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # Skip API routes - let them be handled by the API router
        if full_path.startswith("api/"):
            # This shouldn't happen due to router precedence, but just in case
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not found")
        
        # Check if the requested file exists in static directory (for non-nested assets)
        file_path = os.path.join(static_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        
        # If not a static file, serve index.html for SPA routing
        return FileResponse(os.path.join(static_dir, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# WebSocket endpoint at root so the frontend can connect to the same host
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    """
    Authenticate via `token` query parameter (Auth0 JWT), then attach the
    socket to the authenticated user's connection set. Keeps the socket
    open and ignores client messages except to keep the connection alive.
    """
    # Validate token
    if not token:
        # Reject without accepting to mirror 403 behavior
        await websocket.close(code=1008)
        return

    # Open a DB session manually (can't use Depends with websocket params)
    db = SessionLocal()
    try:
        # Validate JWT and get user
        user = get_user_from_token(token, db)

        # Accept and register connection
        await manager.connect(user.id, websocket)

        try:
            while True:
                # We don't require messages from client; just drain to keep alive
                _ = await websocket.receive_text()
                # Optionally echo pings or ignore
        except WebSocketDisconnect:
            pass
        finally:
            await manager.disconnect(user.id, websocket)
    finally:
        db.close()
