from fastapi import APIRouter
from app.api.endpoints import invitation
from app.api.endpoints import protected

api_router = APIRouter()
api_router.include_router(invitation.router, prefix="/invitations", tags=["invitations"])
api_router.include_router(protected.router, prefix="/protected", tags=["protected"])
