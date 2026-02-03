"""Celery tasks for async pipeline execution"""

import logging
from pathlib import Path
from celery import Celery, Task
from src.ml_engine.kedro_runner import get_executor
from app.core.job_manager import JobManager
from app.models.job_models import JobStatus

# Get absolute project path
PROJECT_PATH = str(Path(__file__).parent.parent.resolve())

# Initialize Celery
celery_app = Celery('ml_platform')
celery_app.config_from_object('celery_config:CeleryConfig')

logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """Task with callback handlers"""

    def on_success(self, retval, task_id, args, kwargs):
        """On task success"""
        logger.info(f"✅ Task {task_id} succeeded")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """On task failure"""
        logger.error(f"❌ Task {task_id} failed: {exc}")


@celery_app.task(base=CallbackTask, bind=True, name='app.tasks.execute_pipeline')
def execute_pipeline_task(self, job_id: str, pipeline_name: str, parameters: dict = None):
    """
    Execute Kedro pipeline as async Celery task

    This runs in background, doesn't block HTTP request
    """

    try:
        logger.info(f"🚀 Starting pipeline execution: {pipeline_name} (Job: {job_id})")

        # Update job status to RUNNING
        manager = JobManager()
        manager.update_job_status(job_id, JobStatus.RUNNING)

        # Execute pipeline - PASS PROJECT PATH
        executor = get_executor(PROJECT_PATH)
        result = executor.execute_pipeline(
            pipeline_name=pipeline_name,
            parameters=parameters,
            run_id=job_id
        )

        # Update job with results
        if result["status"] == "success":
            logger.info(f"✅ Pipeline completed: {pipeline_name}")
            manager.update_job_status(
                job_id,
                JobStatus.COMPLETED,
                results=result.get("outputs"),
                execution_time=int(result.get("execution_time", 0))
            )
        else:
            logger.error(f"❌ Pipeline failed: {result.get('error')}")
            manager.update_job_status(
                job_id,
                JobStatus.FAILED,
                error_message=result.get("error"),
                execution_time=int(result.get("execution_time", 0))
            )

        return result

    except Exception as e:
        logger.error(f"❌ Task execution failed: {e}")
        manager = JobManager()
        manager.update_job_status(
            job_id,
            JobStatus.FAILED,
            error_message=str(e)
        )
        raise


# Optional: Task to check if pipeline exists
@celery_app.task(name='app.tasks.check_pipeline')
def check_pipeline_exists(pipeline_name: str):
    """Check if pipeline exists"""
    executor = get_executor(PROJECT_PATH)  # PASS PROJECT PATH
    pipelines = executor.get_available_pipelines()
    return pipeline_name in pipelines


# Optional: Task to get pipeline details
@celery_app.task(name='app.tasks.get_pipeline_info')
def get_pipeline_info(pipeline_name: str):
    """Get pipeline information"""
    executor = get_executor(PROJECT_PATH)  # PASS PROJECT PATH
    return executor.get_pipeline_details(pipeline_name)