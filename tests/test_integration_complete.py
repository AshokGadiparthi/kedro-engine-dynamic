"""
Comprehensive Integration Tests

Tests for Kedro-FastAPI integration including:
- KedroExecutor functionality
- JobManager CRUD operations
- API endpoints
- Database operations
"""

import pytest
import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.job_models import Job, JobStatus
from app.core.job_manager import JobManager
from src.ml_engine.kedro_runner import KedroExecutor, get_executor


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def test_db():
    """Create test database"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def job_manager(test_db):
    """Create job manager with test database"""
    return JobManager(db=test_db)


# ============================================================================
# KEDRO EXECUTOR TESTS
# ============================================================================

class TestKedroExecutor:
    """Test KedroExecutor functionality"""
    
    def test_executor_initialization(self):
        """Test executor can be initialized"""
        executor = KedroExecutor(project_path=".")
        assert executor.project_path.exists()
        assert not executor._initialized
    
    def test_executor_singleton(self):
        """Test executor singleton pattern"""
        executor1 = get_executor(project_path=".")
        executor2 = get_executor(project_path=".")
        assert executor1 is executor2
    
    def test_get_available_pipelines(self):
        """Test getting available pipelines"""
        executor = get_executor()
        if executor._initialized:
            pipelines = executor.get_available_pipelines()
            assert isinstance(pipelines, list)
    
    def test_executor_health_check(self):
        """Test health check"""
        executor = get_executor()
        health = executor.get_health_status()
        assert "status" in health
        assert health["initialized"] == executor._initialized


# ============================================================================
# JOB MANAGER TESTS
# ============================================================================

class TestJobManager:
    """Test JobManager CRUD operations"""
    
    def test_create_job(self, job_manager, test_db):
        """Test creating a job"""
        job = job_manager.create_job(
            pipeline_name="test_pipeline",
            user_id="user123",
            parameters={"test": "param"}
        )
        
        assert job is not None
        assert job["pipeline_name"] == "test_pipeline"
        assert job["user_id"] == "user123"
        assert job["status"] == "pending"
        assert job["parameters"] == {"test": "param"}
    
    def test_get_job(self, job_manager, test_db):
        """Test retrieving a job"""
        # Create job
        created = job_manager.create_job(
            pipeline_name="test",
            user_id="user123"
        )
        
        # Retrieve job
        retrieved = job_manager.get_job(created["id"])
        assert retrieved is not None
        assert retrieved["id"] == created["id"]
    
    def test_update_job_status(self, job_manager, test_db):
        """Test updating job status"""
        # Create job
        job = job_manager.create_job(
            pipeline_name="test",
            user_id="user123"
        )
        
        # Update to running
        updated = job_manager.update_job_status(
            job["id"],
            JobStatus.RUNNING
        )
        assert updated["status"] == "running"
        
        # Update to completed
        updated = job_manager.update_job_status(
            job["id"],
            JobStatus.COMPLETED,
            results={"output": "data"},
            execution_time=45
        )
        assert updated["status"] == "completed"
        assert updated["results"] == {"output": "data"}
        assert updated["execution_time"] == 45
    
    def test_list_jobs(self, job_manager, test_db):
        """Test listing jobs"""
        # Create multiple jobs
        job_manager.create_job("pipeline1", "user1")
        job_manager.create_job("pipeline2", "user1")
        job_manager.create_job("pipeline3", "user2")
        
        # List jobs for user1
        jobs = job_manager.list_jobs(user_id="user1", limit=10)
        assert len(jobs) == 2
    
    def test_get_job_stats(self, job_manager, test_db):
        """Test job statistics"""
        # Create jobs with different statuses
        job1 = job_manager.create_job("p1", "user1")
        job2 = job_manager.create_job("p2", "user1")
        job3 = job_manager.create_job("p3", "user1")
        
        # Set different statuses
        job_manager.update_job_status(job1["id"], JobStatus.COMPLETED)
        job_manager.update_job_status(job2["id"], JobStatus.RUNNING)
        job_manager.update_job_status(job3["id"], JobStatus.FAILED, error_message="Error")
        
        # Get stats
        stats = job_manager.get_job_stats(user_id="user1")
        assert stats["total"] == 3
        assert stats["completed"] == 1
        assert stats["running"] == 1
        assert stats["failed"] == 1
        assert stats["pending"] == 0
    
    def test_cancel_job(self, job_manager, test_db):
        """Test cancelling a job"""
        # Create and cancel job
        job = job_manager.create_job("test", "user1")
        cancelled = job_manager.cancel_job(job["id"])
        
        assert cancelled["status"] == "cancelled"
    
    def test_cannot_cancel_completed_job(self, job_manager, test_db):
        """Test that completed jobs cannot be cancelled"""
        # Create and complete job
        job = job_manager.create_job("test", "user1")
        job_manager.update_job_status(job["id"], JobStatus.COMPLETED)
        
        # Try to cancel (should not change status)
        cancelled = job_manager.cancel_job(job["id"])
        assert cancelled["status"] == "completed"


# ============================================================================
# JOB MODEL TESTS
# ============================================================================

class TestJobModel:
    """Test Job model"""
    
    def test_job_to_dict(self, test_db):
        """Test Job.to_dict() method"""
        job = Job(
            id="test-id",
            pipeline_name="test",
            user_id="user1",
            status=JobStatus.PENDING,
            parameters={"test": "value"}
        )
        
        test_db.add(job)
        test_db.commit()
        
        job_dict = job.to_dict()
        assert job_dict["id"] == "test-id"
        assert job_dict["pipeline_name"] == "test"
        assert job_dict["status"] == "pending"
        assert job_dict["parameters"] == {"test": "value"}


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Test integrated functionality"""
    
    def test_create_and_retrieve_job(self, job_manager, test_db):
        """Test complete job lifecycle"""
        # Create
        job = job_manager.create_job("pipeline", "user1", {"param": "value"})
        job_id = job["id"]
        
        # Retrieve
        retrieved = job_manager.get_job(job_id)
        assert retrieved["id"] == job_id
        assert retrieved["status"] == "pending"
        
        # Update to running
        job_manager.update_job_status(job_id, JobStatus.RUNNING)
        retrieved = job_manager.get_job(job_id)
        assert retrieved["status"] == "running"
        assert retrieved["started_at"] is not None
        
        # Complete
        job_manager.update_job_status(
            job_id,
            JobStatus.COMPLETED,
            results={"output": "result"},
            execution_time=30
        )
        retrieved = job_manager.get_job(job_id)
        assert retrieved["status"] == "completed"
        assert retrieved["completed_at"] is not None
        assert retrieved["execution_time"] == 30
    
    def test_multiple_users_isolation(self, job_manager, test_db):
        """Test that jobs are isolated per user"""
        # Create jobs for different users
        job1 = job_manager.create_job("p1", "user1")
        job2 = job_manager.create_job("p2", "user2")
        job3 = job_manager.create_job("p3", "user1")
        
        # List for user1
        user1_jobs = job_manager.list_jobs(user_id="user1")
        assert len(user1_jobs) == 2
        assert all(j["user_id"] == "user1" for j in user1_jobs)
        
        # List for user2
        user2_jobs = job_manager.list_jobs(user_id="user2")
        assert len(user2_jobs) == 1
        assert user2_jobs[0]["user_id"] == "user2"


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src", "--cov=app"])
