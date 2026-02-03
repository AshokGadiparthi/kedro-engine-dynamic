"""
Projects API Endpoints
"""

from fastapi import APIRouter, HTTPException
from app.schemas.schemas import ProjectCreate, ProjectResponse
import logging
import uuid

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("")
async def list_projects():
    """List all projects"""
    try:
        logger.info("📋 Listing projects")
        return []
    except Exception as e:
        logger.error(f"❌ Error listing projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=ProjectResponse)
async def create_project(project_data: ProjectCreate):
    """Create new project"""
    try:
        logger.info(f"🆕 Creating project: {project_data.name}")
        
        project_id = str(uuid.uuid4())
        
        return ProjectResponse(
            id=project_id,
            name=project_data.name,
            description=project_data.description,
            owner_id="user_mock",
            created_at="2026-02-03T17:30:00"
        )
    except Exception as e:
        logger.error(f"❌ Error creating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))
