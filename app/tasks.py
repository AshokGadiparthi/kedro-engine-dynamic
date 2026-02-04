"""
Celery task for executing Kedro pipelines (Redis broker + correct Kedro bootstrap)
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

from app.celery_app import celery_app   # ✅ bind tasks to YOUR celery instance
from app.core.job_manager import JobManager

logger = logging.getLogger(__name__)

KEDRO_PROJECT_PATH = Path(
    os.getenv("KEDRO_PROJECT_PATH", "/home/ashok/work/latest/full/kedro_working_project")
).resolve()

db_manager = JobManager()


@celery_app.task(bind=True, name="app.tasks.execute_pipeline", time_limit=600)
def execute_pipeline(self, job_id: str, pipeline_name: str, parameters: dict | None = None):
    if parameters is None:
        parameters = {}

    try:
        logger.info("=" * 80)
        logger.info("🚀 STARTING PIPELINE EXECUTION")
        logger.info("=" * 80)
        logger.info(f"Job ID: {job_id}")
        logger.info(f"Pipeline: {pipeline_name}")
        logger.info(f"Parameters: {parameters}")

        # STEP 1: update status
        db_manager.update_job_status(job_id, "running")

        # STEP 2: verify Kedro project exists
        if not KEDRO_PROJECT_PATH.exists():
            raise FileNotFoundError(f"Kedro project not found at {KEDRO_PROJECT_PATH}")

        # STEP 3: add src to path
        project_src = str(KEDRO_PROJECT_PATH / "src")
        if project_src not in sys.path:
            sys.path.insert(0, project_src)

        # STEP 4: bootstrap Kedro project correctly
        from kedro.framework.startup import bootstrap_project
        from kedro.framework.project import configure_project
        from kedro.framework.session import KedroSession

        metadata = bootstrap_project(KEDRO_PROJECT_PATH)
        configure_project(metadata.package_name)  # ✅ package name, not path

        # STEP 5: run pipeline
        start_time = datetime.utcnow()
        with KedroSession.create(project_path=KEDRO_PROJECT_PATH) as session:
            session.run(pipeline_name=pipeline_name)

        execution_time = (datetime.utcnow() - start_time).total_seconds()

        result = {
            "status": "completed",
            "job_id": job_id,
            "pipeline_name": pipeline_name,
            "execution_time": execution_time,
            "message": f"Pipeline '{pipeline_name}' executed successfully",
            "timestamp": datetime.utcnow().isoformat(),
            "parameters_used": parameters,
        }

        # STEP 6: update DB
        db_manager.update_job_status(job_id, "completed")
        db_manager.update_job_result(job_id, result)

        logger.info("✅ PIPELINE EXECUTION SUCCESSFUL")
        return result

    except Exception as e:
        logger.exception("❌ PIPELINE EXECUTION FAILED")

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
        except Exception:
            pass

        raise
