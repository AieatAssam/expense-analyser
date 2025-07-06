from fastapi import APIRouter

api_router = APIRouter()

# Import and include specific API endpoints here
# Example: from app.api.endpoints import users
# api_router.include_router(users.router, prefix="/users", tags=["users"])

# Health check endpoint will be in the main app
