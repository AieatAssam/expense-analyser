from fastapi import APIRouter
from app.api.endpoints import invitation, protected, receipt, receipt_processing, analytics, export, health, receipt_editing, users

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(invitation.router, prefix="/invitations", tags=["invitations"])
api_router.include_router(protected.router, prefix="/protected", tags=["protected"])
api_router.include_router(receipt.router, prefix="/receipts", tags=["receipts"])
api_router.include_router(receipt_processing.router, prefix="/receipts", tags=["receipt-processing"])
api_router.include_router(receipt_editing.router, prefix="/receipts/edit", tags=["receipt-editing"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
