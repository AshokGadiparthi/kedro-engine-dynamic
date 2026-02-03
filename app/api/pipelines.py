"""
Pipeline Management Endpoints

Exposes Kedro pipeline discovery and metadata via REST API.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import logging

from src.ml_engine.kedro_runner import get_executor
from app.core.auth import get_current_user

# TO (for development without auth):
from app.core.auth import get_mock_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/pipelines", tags=["Pipelines"])


@router.get("", summary="List all pipelines")
async def list_pipelines(current_user: Dict = Depends(get_current_user)):
    """Get all available Kedro pipelines"""
    try:
        executor = get_executor()
        pipelines = executor.get_available_pipelines()
        
        return {
            "count": len(pipelines),
            "pipelines": [{"name": p} for p in pipelines]
        }
    except Exception as e:
        logger.error(f"Error listing pipelines: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{pipeline_name}", summary="Get pipeline details")
async def get_pipeline_details(pipeline_name: str):
    """Get detailed information about a specific pipeline"""
    try:
        executor = get_executor()
        details = executor.get_pipeline_details(pipeline_name)
        
        if "error" in details:
            raise HTTPException(status_code=404, detail=details["error"])
        
        return details
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pipeline details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{pipeline_name}/parameters", summary="Get pipeline parameters")
async def get_pipeline_parameters(pipeline_name: str):
    """Get default parameters for a pipeline"""
    try:
        executor = get_executor()
        params = executor.get_pipeline_parameters(pipeline_name)
        
        if "error" in params:
            raise HTTPException(status_code=404, detail=params["error"])
        
        return {
            "pipeline_name": pipeline_name,
            "parameters": params
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting parameters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", summary="Health check")
async def health_check():
    """Check Kedro integration health"""
    try:
        executor = get_executor()
        return executor.get_health_status()
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}
