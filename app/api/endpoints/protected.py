
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from app.core.auth import get_current_user

router = APIRouter()

@router.get("/protected")
def protected_route(current_user=Depends(get_current_user)):
    return {"message": f"Hello, {current_user.email}. This is a protected route."}

# Dummy switch-account endpoint for testing
@router.get("/switch-account")
def switch_account(current_user=Depends(get_current_user)):
    return {"message": f"Switched account for {current_user.email}"}

# Dummy logout endpoint for testing
@router.post("/logout")
def logout(current_user=Depends(get_current_user)):
    return JSONResponse(content={"message": f"Logged out {current_user.email}"})
