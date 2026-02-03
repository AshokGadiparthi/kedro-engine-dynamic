"""
Job Management System

Manages the lifecycle of pipeline execution jobs.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.job_models import Job, JobStatus

logger = logging.getLogger(__name__)


class JobManager:
    """Manage pipeline execution jobs."""
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize job manager."""
        self.db = db or SessionLocal()
    
    def create_job(
        self,
        pipeline_name: str,
        user_id: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new job record."""
        try:
            job_id = str(uuid.uuid4())
            
            job = Job(
                id=job_id,
                pipeline_name=pipeline_name,
                user_id=user_id,
                status=JobStatus.PENDING,
                parameters=parameters or {},
                created_at=datetime.utcnow()
            )
            
            self.db.add(job)
            self.db.commit()
            self.db.refresh(job)
            
            logger.info(f"✅ Job created: {job_id}")
            return job.to_dict()
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Failed to create job: {e}")
            raise
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID."""
        job = self.db.query(Job).filter(Job.id == job_id).first()
        return job.to_dict() if job else None
    
    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        error_message: Optional[str] = None,
        results: Optional[Dict[str, Any]] = None,
        execution_time: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Update job status."""
        try:
            job = self.db.query(Job).filter(Job.id == job_id).first()
            
            if not job:
                logger.warning(f"Job not found: {job_id}")
                return None
            
            job.status = status
            
            if status == JobStatus.RUNNING:
                job.started_at = datetime.utcnow()
            
            if status == JobStatus.COMPLETED:
                job.completed_at = datetime.utcnow()
                job.results = results
                job.execution_time = execution_time
            
            if status == JobStatus.FAILED:
                job.completed_at = datetime.utcnow()
                job.error_message = error_message
                job.execution_time = execution_time
            
            self.db.commit()
            self.db.refresh(job)
            
            logger.info(f"✅ Job {job_id} status updated to {status}")
            return job.to_dict()
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Failed to update job status: {e}")
            raise
    
    def list_jobs(
        self,
        user_id: Optional[str] = None,
        status: Optional[JobStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List jobs with optional filters."""
        query = self.db.query(Job)
        
        if user_id:
            query = query.filter(Job.user_id == user_id)
        
        if status:
            query = query.filter(Job.status == status)
        
        jobs = query.order_by(Job.created_at.desc()).limit(limit).offset(offset).all()
        
        return [job.to_dict() for job in jobs]
    
    def get_job_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get job statistics."""
        query = self.db.query(Job)
        
        if user_id:
            query = query.filter(Job.user_id == user_id)
        
        total = query.count()
        
        return {
            "total": total,
            "pending": query.filter(Job.status == JobStatus.PENDING).count(),
            "running": query.filter(Job.status == JobStatus.RUNNING).count(),
            "completed": query.filter(Job.status == JobStatus.COMPLETED).count(),
            "failed": query.filter(Job.status == JobStatus.FAILED).count(),
            "cancelled": query.filter(Job.status == JobStatus.CANCELLED).count()
        }
    
    def cancel_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Cancel a job."""
        try:
            job = self.db.query(Job).filter(Job.id == job_id).first()
            
            if not job:
                return None
            
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                logger.warning(f"Cannot cancel job {job_id}: already {job.status}")
                return job.to_dict()
            
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(job)
            
            logger.info(f"✅ Job {job_id} cancelled")
            return job.to_dict()
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Failed to cancel job: {e}")
            raise
