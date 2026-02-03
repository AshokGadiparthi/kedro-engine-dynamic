"""
Authentication and authorization module
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer security
security = HTTPBearer()


class Token(BaseModel):
    """Token schema"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data schema"""
    username: Optional[str] = None
    user_id: Optional[str] = None


class User(BaseModel):
    """User schema"""
    id: str
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    """User in database schema"""
    hashed_password: str


# ============================================================================
# PASSWORD FUNCTIONS
# ============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against hashed password"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


# ============================================================================
# TOKEN FUNCTIONS
# ============================================================================

def create_access_token(
        data: dict,
        expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token"""

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating token: {e}")
        raise


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode JWT token"""

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"Invalid token: {e}")
        return None


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_current_user(
        credentials: HTTPAuthCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Get current user from JWT token
    
    This is used as a dependency in FastAPI endpoints:
    
    @router.get("/protected")
    async def protected_route(current_user: Dict = Depends(get_current_user)):
        return current_user
    """

    token = credentials.credentials

    # Decode token
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user info
    user_id: str = payload.get("sub")
    username: str = payload.get("username")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Return user data
    return {
        "id": user_id,
        "username": username,
        "email": payload.get("email"),
        "full_name": payload.get("full_name"),
    }


def get_current_user_optional(
        credentials: Optional[HTTPAuthCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    Get current user (optional - doesn't fail if not authenticated)
    
    Used for endpoints that work with or without auth
    """

    if credentials is None:
        return None

    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        return None

    return {
        "id": payload.get("sub"),
        "username": payload.get("username"),
        "email": payload.get("email"),
        "full_name": payload.get("full_name"),
    }


# ============================================================================
# DEMO USER FUNCTIONS (For Testing)
# ============================================================================

async def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate user (Demo version)
    
    In production, query database and verify password
    """

    # Demo: hardcoded user for testing
    # In production, query database
    demo_users = {
        "admin": {
            "id": "user-001",
            "username": "admin",
            "email": "admin@example.com",
            "full_name": "Admin User",
            "hashed_password": get_password_hash("admin123"),
        }
    }

    if username not in demo_users:
        return None

    user = demo_users[username]

    if not verify_password(password, user["hashed_password"]):
        return None

    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "full_name": user["full_name"],
    }


async def login_for_access_token(username: str, password: str) -> Dict[str, str]:
    """
    Login endpoint to get access token
    
    Usage:
    @router.post("/login")
    async def login(username: str, password: str):
        return await login_for_access_token(username, password)
    """

    user = await authenticate_user(username, password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user["id"], "username": user["username"], "email": user.get("email")}
    )

    return {"access_token": access_token, "token_type": "bearer"}


# ============================================================================
# MOCK USER FOR DEVELOPMENT
# ============================================================================

class MockUser:
    """Mock user for development without auth"""

    id = "dev-user-001"
    username = "developer"
    email = "dev@example.com"
    full_name = "Developer"
    disabled = False


async def get_mock_user() -> Dict[str, Any]:
    """Get mock user (for testing without auth)"""
    return {
        "id": MockUser.id,
        "username": MockUser.username,
        "email": MockUser.email,
        "full_name": MockUser.full_name,
    }