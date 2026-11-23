"""
SentinelX Security & Authentication Layer
Implements JWT token generation, password verification, and Role-Based Access Control (RBAC).
"""

from datetime import datetime, timedelta
from typing import Optional, List
import jwt
from fastapi import HTTPException, Security, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.app.config import settings

security = HTTPBearer(auto_error=False)

# Seed user credentials
DEMO_USERS = {
    "analyst": {
        "user_id": "USR_101",
        "username": "analyst",
        "password": "sentinelx123",
        "role": "ANALYST",
        "name": "Priyam, Lead Fraud Intelligence Specialist"
    },
    "admin": {
        "user_id": "USR_999",
        "username": "admin",
        "password": "admin123",
        "role": "ADMIN",
        "name": "Alexander Vance, Risk Director"
    }
}

def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = DEMO_USERS.get(username)
    if user and user["password"] == password:
        return user
    return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> dict:
    # Allow seamless development usage if no token provided
    if not credentials:
        return DEMO_USERS["analyst"]
        
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None or username not in DEMO_USERS:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token credentials"
            )
        return DEMO_USERS[username]
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

def require_role(allowed_roles: List[str]):
    def role_checker(user: dict = Depends(get_current_user)):
        if user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of the roles: {allowed_roles}"
            )
        return user
    return role_checker
