"""
COPY THIS ENTIRE FILE TO: app/core/auth.py

This is the FIXED version that works with all FastAPI versions
No HTTPBearer import issues!
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from fastapi import Depends, HTTPException, status, Header
from jose import JWTError, jwt
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============================================================================
# MAIN FUNCTION - USE THIS IN YOUR ENDPOINTS
# ============================================================================

def get_current_user(
        authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """Get current user from Bearer token"""

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token from "Bearer <token>"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid scheme")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Use: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Decode token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "id": user_id,
        "username": payload.get("username", "unknown"),
        "email": payload.get("email"),
        "full_name": payload.get("full_name"),
    }


# ============================================================================
# FOR DEVELOPMENT - NO AUTH REQUIRED
# ============================================================================

def get_mock_user() -> Dict[str, Any]:
    """Mock user for development"""
    return {
        "id": "dev-user-001",
        "username": "developer",
        "email": "dev@example.com",
        "full_name": "Developer",
    }


# ============================================================================
# OPTIONAL AUTH
# ============================================================================

def get_current_user_optional(
        authorization: Optional[str] = Header(None)
) -> Optional[Dict[str, Any]]:
    """Optional authentication"""

    if not authorization:
        return None

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
    except ValueError:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if user_id is None:
            return None

        return {
            "id": user_id,
            "username": payload.get("username", "unknown"),
            "email": payload.get("email"),
            "full_name": payload.get("full_name"),
        }
    except JWTError:
        return None


# ============================================================================
# HELPERS
# ============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def login_for_access_token(username: str, password: str) -> Dict[str, str]:
    """Login endpoint"""

    if username == "admin" and password == "admin123":
        access_token = create_access_token(
            data={
                "sub": "user-001",
                "username": "admin",
                "email": "admin@example.com",
                "full_name": "Admin User"
            }
        )
        return {"access_token": access_token, "token_type": "bearer"}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
    )