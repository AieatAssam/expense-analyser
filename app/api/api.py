from fastapi import APIRouter

api_router = APIRouter()


# Import and include invitation endpoints
from app.api.endpoints import invitation
api_router.include_router(invitation.router, prefix="/invitations", tags=["invitations"])

# Health check endpoint will be in the main app
