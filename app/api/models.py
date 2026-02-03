"""
Models API Endpoints
"""

from fastapi import APIRouter, HTTPException
from app.schemas.schemas import ModelCreate, ModelResponse
import logging
import uuid

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("")
async def list_models():
    """List all models"""
    try:
        logger.info("📋 Listing models")
        return []
    except Exception as e:
        logger.error(f"❌ Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=ModelResponse)
async def create_model(model_data: ModelCreate):
    """Create new model"""
    try:
        logger.info(f"🆕 Creating model: {model_data.name}")
        
        model_id = str(uuid.uuid4())
        
        return ModelResponse(
            id=model_id,
            name=model_data.name,
            project_id=model_data.project_id,
            description=model_data.description,
            model_type=model_data.model_type,
            created_at="2026-02-03T17:30:00"
        )
    except Exception as e:
        logger.error(f"❌ Error creating model: {e}")
        raise HTTPException(status_code=500, detail=str(e))
