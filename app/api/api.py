from fastapi import APIRouter
from app.api.endpoints import invitation, protected, receipt

api_router = APIRouter()
api_router.include_router(invitation.router, prefix="/invitations", tags=["invitations"])
api_router.include_router(protected.router, prefix="/protected", tags=["protected"])
api_router.include_router(receipt.router, prefix="/receipts", tags=["receipts"])
