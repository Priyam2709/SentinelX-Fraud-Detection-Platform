"""
SentinelX Authentication Routes
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any

from backend.app.models.schemas import UserLogin, TokenResponse
from backend.app.security.authentication import authenticate_user, create_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin):
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password. Demo accounts: analyst / sentinelx123 or admin / admin123"
        )
        
    token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_role": user["role"],
        "username": user["username"]
    }
