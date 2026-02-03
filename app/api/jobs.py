"""
Job Management Endpoints

Manages pipeline execution jobs and their lifecycle.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional
import logging

from src.ml_engine.kedro_runner import get_executor
from app.core.job_manager import JobManager
from app.models.job_models import JobStatus
from app.schemas.job_schemas import JobCreate, JobResponse, JobListResponse, JobStatsResponse
from app.core.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])


@router.post("", response_model=JobResponse, summary="Submit a job", status_code=202)
async def submit_job(
    job_data: JobCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Submit a pipeline for execution"""
    try:
        # Verify pipeline exists
        executor = get_executor()
        pipelines = executor.get_available_pipelines()
        
        if job_data.pipeline_name not in pipelines:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline '{job_data.pipeline_name}' not found"
            )
        
        # Create job record
        manager = JobManager()
        job = manager.create_job(
            pipeline_name=job_data.pipeline_name,
            user_id=current_user.get("id", "anonymous"),
            parameters=job_data.parameters
        )
        
        logger.info(f"Job submitted: {job['id']}")
        return job
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}", response_model=JobResponse, summary="Get job status")
async def get_job_status(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get the status of a job"""
    try:
        manager = JobManager()
        job = manager.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Check ownership
        if job["user_id"] != current_user.get("id", "anonymous") and current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Not authorized")
        
        return job
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/results", summary="Get job results")
async def get_job_results(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get the results of a completed job"""
    try:
        manager = JobManager()
        job = manager.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job["status"] not in ["completed", "failed"]:
            raise HTTPException(
                status_code=400,
                detail=f"Job is still {job['status']}"
            )
        
        return {
            "status": job["status"],
            "execution_time": job["execution_time"],
            "results": job["results"],
            "error": job["error_message"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=JobListResponse, summary="List jobs")
async def list_jobs(
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List jobs for the current user"""
    try:
        manager = JobManager()
        
        job_status = None
        if status:
            try:
                job_status = JobStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        jobs = manager.list_jobs(
            user_id=current_user.get("id", "anonymous"),
            status=job_status,
            limit=limit,
            offset=offset
        )
        
        total = manager.db.query(JobStatus).filter(
            JobStatus.user_id == current_user.get("id")
        ).count()
        
        return {
            "total": total,
            "jobs": jobs,
            "limit": limit,
            "offset": offset
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{job_id}/cancel", summary="Cancel a job")
async def cancel_job(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Cancel a running job"""
    try:
        manager = JobManager()
        job = manager.cancel_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {
            "id": job["id"],
            "status": job["status"],
            "message": "Job cancelled successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=JobStatsResponse, summary="Get job statistics")
async def get_job_stats(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get statistics about jobs"""
    try:
        manager = JobManager()
        stats = manager.get_job_stats(user_id=current_user.get("id", "anonymous"))
        return stats
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
