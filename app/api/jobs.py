"""
Jobs API Endpoints
Pipeline job submission and status tracking
"""

from fastapi import APIRouter, HTTPException
from app.schemas.schemas import JobCreate, JobResponse
from app.tasks import execute_pipeline_task
from app.core.job_manager import JobManager
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/api/v1/jobs", response_model=JobResponse, status_code=202)
async def submit_job(job_data: JobCreate):
    """Submit a pipeline for execution (async with Celery)"""
    try:
        logger.info(f"🚀 Job submission started")
        
        # Create job record
        manager = JobManager()
        job = manager.create_job(
            pipeline_name=job_data.pipeline_name,
            user_id="anonymous",
            parameters=job_data.parameters
        )
        
        logger.info(f"✅ Job created: {job['id']}")
        
        # Send to Celery
        logger.info(f"📤 Sending task to Celery...")
        
        task = execute_pipeline_task.delay(
            job_id=job["id"],
            pipeline_name=job_data.pipeline_name,
            parameters=job_data.parameters
        )
        
        logger.info(f"✅ Task sent! Task ID: {task.id}")
        
        return job
    
    except Exception as e:
        logger.error(f"❌ Error submitting job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    """Get job status (non-blocking)"""
    try:
        manager = JobManager()
        job = manager.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return job
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
