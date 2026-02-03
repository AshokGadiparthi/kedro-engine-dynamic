"""
Activities API Endpoints
"""

from fastapi import APIRouter, HTTPException
from app.schemas.schemas import ActivityCreate, ActivityResponse
import logging
import uuid

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("")
async def list_activities():
    """List all activities"""
    try:
        logger.info("📋 Listing activities")
        return []
    except Exception as e:
        logger.error(f"❌ Error listing activities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=ActivityResponse)
async def create_activity(activity_data: ActivityCreate):
    """Create new activity"""
    try:
        logger.info(f"📝 Creating activity: {activity_data.action}")
        
        activity_id = str(uuid.uuid4())
        
        return ActivityResponse(
            id=activity_id,
            user_id="user_mock",
            action=activity_data.action,
            entity_type=activity_data.entity_type,
            entity_id=activity_data.entity_id,
            details=activity_data.details,
            created_at="2026-02-03T17:30:00"
        )
    except Exception as e:
        logger.error(f"❌ Error creating activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))
