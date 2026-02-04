"""
Fixed Celery task for executing Kedro pipelines
This version properly handles Kedro execution without blocking
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from celery import shared_task
from app.core.job_manager import JobManager

logger = logging.getLogger(__name__)

# Get Kedro project path from environment or default
KEDRO_PROJECT_PATH = Path(os.getenv(
    'KEDRO_PROJECT_PATH',
    '/home/ashok/work/latest/full/kedro_working_project'
))

# Initialize job manager
db_manager = JobManager()


@shared_task(bind=True, name='app.tasks.execute_pipeline', time_limit=600)
def execute_pipeline(self, job_id: str, pipeline_name: str, parameters: dict = None):
    """
    Execute a Kedro pipeline

    Args:
        job_id: Job ID
        pipeline_name: Name of pipeline to execute
        parameters: Pipeline parameters

    Returns:
        Result dict
    """
    if parameters is None:
        parameters = {}

    try:
        logger.info("=" * 80)
        logger.info("🚀 STARTING PIPELINE EXECUTION")
        logger.info("=" * 80)
        logger.info(f"Job ID: {job_id}")
        logger.info(f"Pipeline: {pipeline_name}")
        logger.info(f"Parameters: {parameters}")
        logger.info("")

        # =========================================================================
        # STEP 1: Update job status
        # =========================================================================
        logger.info("[STEP 1] Updating job status...")
        try:
            db_manager.update_job_status(job_id, "running")
            logger.info(f"✅ Job {job_id} marked as RUNNING")
        except Exception as e:
            logger.error(f"❌ Failed to update job status: {e}")
            raise

        logger.info("")

        # =========================================================================
        # STEP 2: Verify Kedro project exists
        # =========================================================================
        logger.info("[STEP 2] Verifying Kedro project...")
        if not KEDRO_PROJECT_PATH.exists():
            raise FileNotFoundError(f"Kedro project not found at {KEDRO_PROJECT_PATH}")
        logger.info(f"✅ Kedro project verified: {KEDRO_PROJECT_PATH}")

        logger.info("")

        # =========================================================================
        # STEP 3: Add Kedro project to Python path
        # =========================================================================
        logger.info("[STEP 3] Adding Kedro project to Python path...")
        project_src = str(KEDRO_PROJECT_PATH / "src")
        if project_src not in sys.path:
            sys.path.insert(0, project_src)
        logger.info(f"✅ Added to path: {project_src}")

        logger.info("")

        # =========================================================================
        # STEP 4: Import Kedro and load project
        # =========================================================================
        logger.info("[STEP 4] Loading Kedro project...")
        try:
            # Import AFTER adding to path
            from kedro.framework.project import configure_project, ProjectNotFound
            from kedro.framework.session import KedroSession

            # This is the key - configure project, don't load session yet
            logger.info(f"Configuring project from: {KEDRO_PROJECT_PATH}")
            configure_project(str(KEDRO_PROJECT_PATH))
            logger.info("✅ Kedro project configured")

        except ImportError as e:
            logger.error(f"❌ Failed to import Kedro: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to configure project: {e}")
            raise

        logger.info("")

        # =========================================================================
        # STEP 5: Execute pipeline
        # =========================================================================
        logger.info("[STEP 5] Executing pipeline...")
        start_time = datetime.utcnow()

        try:
            # Create session and run pipeline
            with KedroSession.create(str(KEDRO_PROJECT_PATH)) as session:
                logger.info(f"Session created, running pipeline: {pipeline_name}")

                runner = session.run(
                    pipeline_name=pipeline_name,
                    tags=None,
                    runner=None,
                )

                logger.info(f"✅ Pipeline execution completed")

        except Exception as e:
            logger.error(f"❌ Pipeline execution failed: {e}")
            raise

        execution_time = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Execution time: {execution_time:.2f}s")

        logger.info("")

        # =========================================================================
        # STEP 6: Prepare result
        # =========================================================================
        logger.info("[STEP 6] Preparing result...")
        result = {
            "status": "completed",
            "job_id": job_id,
            "pipeline_name": pipeline_name,
            "execution_time": execution_time,
            "message": f"Pipeline '{pipeline_name}' executed successfully",
            "timestamp": datetime.utcnow().isoformat(),
            "parameters_used": parameters,
        }
        logger.info(f"✅ Result prepared: {result}")

        logger.info("")

        # =========================================================================
        # STEP 7: Update job in database
        # =========================================================================
        logger.info("[STEP 7] Updating job in database...")
        try:
            db_manager.update_job_status(job_id, "completed")
            db_manager.update_job_result(job_id, result)
            logger.info("✅ Job updated in database")
        except Exception as e:
            logger.error(f"❌ Failed to update job: {e}")
            # Don't raise - job already completed

        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ PIPELINE EXECUTION SUCCESSFUL")
        logger.info("=" * 80)
        logger.info("")

        return result

    except Exception as e:
        logger.error("=" * 80)
        logger.error("❌ PIPELINE EXECUTION FAILED")
        logger.error("=" * 80)
        logger.error(f"Error: {str(e)}", exc_info=True)
        logger.error("")

        # Update job status to failed
        try:
            error_result = {
                "status": "failed",
                "job_id": job_id,
                "pipeline_name": pipeline_name,
                "message": f"Pipeline execution failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            }
            db_manager.update_job_status(job_id, "failed")
            db_manager.update_job_result(job_id, error_result)
        except:
            pass

        raise