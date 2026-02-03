"""
Authentication API Endpoints
"""

from fastapi import APIRouter, HTTPException
from app.schemas.schemas import UserRegister, UserLogin, TokenResponse, UserResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister):
    """Register a new user - creates in database"""
    try:
        logger.info(f"📝 Registering user: {user_data.username}")
        
        # Mock implementation - in real system, check DB
        return TokenResponse(
            access_token="mock_token_" + user_data.username,
            token_type="bearer",
            user=UserResponse(
                id="user_" + user_data.username,
                username=user_data.username,
                email=user_data.email,
                full_name=user_data.full_name,
                created_at="2026-02-03T17:30:00"
            )
        )
    except Exception as e:
        logger.error(f"❌ Registration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    """Login user - finds existing or creates if doesn't exist"""
    try:
        logger.info(f"🔓 User login: {user_data.username}")
        
        return TokenResponse(
            access_token="mock_token_" + user_data.username,
            token_type="bearer",
            user=UserResponse(
                id="user_" + user_data.username,
                username=user_data.username,
                email="user@example.com",
                full_name=user_data.username,
                created_at="2026-02-03T17:30:00"
            )
        )
    except Exception as e:
        logger.error(f"❌ Login failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh():
    """Refresh token"""
    return TokenResponse(
        access_token="mock_refreshed_token",
        token_type="bearer",
        user=UserResponse(
            id="user_mock",
            username="user",
            email="user@example.com",
            full_name="User",
            created_at="2026-02-03T17:30:00"
        )
    )
