"""Job management endpoints - updated with Celery"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional
import logging

from app.tasks import execute_pipeline_task  # ← NEW IMPORT
from app.core.job_manager import JobManager
from app.models.job_models import JobStatus
from app.schemas.job_schemas import JobCreate, JobResponse
from app.core.auth import get_current_user, get_mock_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])


@router.post("/api/v1/jobs", response_model=JobResponse, status_code=202)
async def submit_job(
        job_data: JobCreate,
        current_user: Dict[str, Any] = Depends(get_mock_user)
):
    """Submit a pipeline for execution (async with Celery)"""

    try:
        logger.info(f"🚀 Job submission started")

        # Create job record
        manager = JobManager()
        job = manager.create_job(
            pipeline_name=job_data.pipeline_name,
            user_id=current_user.get("id", "anonymous"),
            parameters=job_data.parameters
        )

        logger.info(f"✅ Job created: {job['id']}")

        # SEND TO CELERY
        logger.info(f"📤 Sending task to Celery...")

        task = execute_pipeline_task.delay(
            job_id=job["id"],
            pipeline_name=job_data.pipeline_name,
            parameters=job_data.parameters
        )

        logger.info(f"✅ Task sent! Task ID: {task.id}")
        logger.info(f"   Task state: {task.state}")

        return job

    except Exception as e:
        logger.error(f"❌ Error submitting job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(
        job_id: str,
        current_user: Dict[str, Any] = Depends(get_mock_user)
):
    """Get job status (non-blocking)"""

    manager = JobManager()
    job = manager.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Job status updates in background
    # Status will be: pending → running → completed/failed
    return job