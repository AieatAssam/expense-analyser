from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.core.config import settings
from app.core.middleware import RequestLoggingMiddleware
from app.api.api import api_router
from app.core.health import get_health_status

app = FastAPI(
    title="Expense Analyser API",
    description="API for expense receipt analysis and tracking",
    version="0.1.0",
)

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
    # Import FileResponse here to avoid cluttering global imports
    from fastapi.responses import FileResponse
    
    # Serve the index.html at the root
    @app.get("/", include_in_schema=False)
    async def read_root():
        return FileResponse(os.path.join(static_dir, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
