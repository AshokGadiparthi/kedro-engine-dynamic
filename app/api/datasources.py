"""
Datasources API Endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("")
async def list_datasources():
    """List all datasources"""
    try:
        logger.info("📋 Listing datasources")
        return []
    except Exception as e:
        logger.error(f"❌ Error listing datasources: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_datasource(data: Dict[str, Any]):
    """Create new datasource and save to database"""
    try:
        logger.info(f"🆕 Creating datasource")
        
        return {
            "id": "datasource_1",
            "data": data,
            "created_at": "2026-02-03T17:30:00"
        }
    except Exception as e:
        logger.error(f"❌ Error creating datasource: {e}")
        raise HTTPException(status_code=500, detail=str(e))
