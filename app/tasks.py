"""
Celery tasks for ML Pipeline execution with Kedro integration
FIXED: Validates pipeline names and adds timeout protection
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from celery_app import app
from kedro.framework.session import KedroSession
from kedro.framework.project import configure_project
from kedro.runner import SequentialRunner
from app.core.job_manager import JobManager

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize DB manager
db_manager = JobManager()

# Get Kedro project path from environment
KEDRO_PROJECT_PATH = Path(os.getenv(
    'KEDRO_PROJECT_PATH',
    '/home/ashok/work/latest/full/kedro_working_project'
))

logger.info(f"✅ Kedro project path configured: {KEDRO_PROJECT_PATH}")

# Valid pipeline names - MUST match your Kedro pipelines!
VALID_PIPELINES = ['hello_world', 'data_pipeline', '__default__']


def get_available_pipelines():
    """Get list of available pipelines from Kedro project"""
    try:
        with KedroSession.create(project_path=KEDRO_PROJECT_PATH) as session:
            return list(session.list_pipelines())
    except Exception as e:
        logger.warning(f"Could not fetch pipelines: {e}")
        return VALID_PIPELINES


@app.task(name='app.tasks.execute_pipeline', bind=True, time_limit=600)
def execute_pipeline(self, job_id: str, pipeline_name: str, parameters: dict = None):
    """
    Execute a Kedro pipeline and store results in database

    FIXED: Now validates pipeline name before execution
    """

    job_start_time = datetime.utcnow()
    logger.info(f"{'='*80}")
    logger.info(f"🚀 STARTING PIPELINE EXECUTION")
    logger.info(f"{'='*80}")
    logger.info(f"Job ID: {job_id}")
    logger.info(f"Pipeline: {pipeline_name}")
    logger.info(f"Parameters: {parameters or {}}")

    try:
        # ====================================================================
        # STEP 1: Update job status
        # ====================================================================
        logger.info(f"\n[STEP 1] Updating job status...")
        db_manager.update_job_status(job_id, "running")
        logger.info(f"✅ Job {job_id} marked as RUNNING")

        # ====================================================================
        # STEP 2: Verify Kedro project exists
        # ====================================================================
        logger.info(f"\n[STEP 2] Verifying Kedro project...")
        if not KEDRO_PROJECT_PATH.exists():
            raise FileNotFoundError(f"Kedro project not found at {KEDRO_PROJECT_PATH}")
        logger.info(f"✅ Kedro project verified: {KEDRO_PROJECT_PATH}")

        # ====================================================================
        # STEP 2.5: VALIDATE PIPELINE NAME (NEW!)
        # ====================================================================
        logger.info(f"\n[STEP 2.5] Validating pipeline name...")

        # Check if pipeline name is a UUID (wrong!)
        if '-' in pipeline_name and len(pipeline_name) == 36:
            logger.error(f"❌ Invalid pipeline name: '{pipeline_name}'")
            logger.error(f"   Pipeline name appears to be a UUID, not a valid pipeline name!")
            logger.error(f"   Valid pipelines: {VALID_PIPELINES}")
            raise ValueError(
                f"Invalid pipeline name '{pipeline_name}'. "
                f"Valid pipelines are: {', '.join(VALID_PIPELINES)}"
            )

        # Check if pipeline name is valid
        if pipeline_name not in VALID_PIPELINES:
            logger.error(f"❌ Pipeline '{pipeline_name}' not found!")
            logger.error(f"   Valid pipelines: {VALID_PIPELINES}")
            raise ValueError(
                f"Pipeline '{pipeline_name}' not found. "
                f"Valid pipelines are: {', '.join(VALID_PIPELINES)}"
            )

        logger.info(f"✅ Pipeline name is valid: {pipeline_name}")

        # ====================================================================
        # STEP 3: Configure and Create Kedro session
        # ====================================================================
        logger.info(f"\n[STEP 3] Configuring Kedro project...")
        logger.info(f"Loading project from {KEDRO_PROJECT_PATH}")

        configure_project(str(KEDRO_PROJECT_PATH))
        logger.info(f"✅ Kedro project configured successfully")

        logger.info(f"\nCreating Kedro session...")
        with KedroSession.create(project_path=KEDRO_PROJECT_PATH) as session:
            logger.info(f"✅ Kedro session created successfully")

            # ================================================================
            # STEP 4: Prepare parameters
            # ================================================================
            logger.info(f"\n[STEP 4] Preparing pipeline parameters...")
            extra_params = parameters or {}

            if extra_params:
                logger.info(f"📊 Using custom parameters:")
                for key, value in extra_params.items():
                    logger.info(f"   - {key}: {value}")
            else:
                logger.info(f"✅ Using default parameters")

            # ================================================================
            # STEP 5: Execute pipeline
            # ================================================================
            logger.info(f"\n[STEP 5] Executing pipeline: {pipeline_name}")
            logger.info(f"{'='*80}")

            try:
                session.run(
                    pipeline_name=pipeline_name,
                    runner_class=SequentialRunner,
                    extra_params=extra_params
                )
                logger.info(f"{'='*80}")
                logger.info(f"✅ Pipeline execution COMPLETED")

            except Exception as pipeline_error:
                logger.error(f"{'='*80}")
                logger.error(f"❌ Pipeline execution FAILED: {str(pipeline_error)}")
                raise

        # ====================================================================
        # STEP 6: Prepare result
        # ====================================================================
        logger.info(f"\n[STEP 6] Preparing execution result...")

        execution_time = (datetime.utcnow() - job_start_time).total_seconds()

        result = {
            "status": "completed",
            "pipeline_name": pipeline_name,
            "message": f"Pipeline '{pipeline_name}' executed successfully",
            "execution_time": execution_time,
            "parameters_used": extra_params,
            "timestamp": job_start_time.isoformat()
        }

        logger.info(f"✅ Result prepared:")
        logger.info(f"   - Status: {result['status']}")
        logger.info(f"   - Execution Time: {execution_time:.2f}s")

        # ====================================================================
        # STEP 7: Store results in database
        # ====================================================================
        logger.info(f"\n[STEP 7] Storing results in database...")

        db_manager.update_job_results(job_id, result)
        logger.info(f"✅ Results stored for job {job_id}")

        # ====================================================================
        # SUCCESS
        # ====================================================================
        logger.info(f"\n{'='*80}")
        logger.info(f"✅ PIPELINE EXECUTION SUCCESSFUL")
        logger.info(f"{'='*80}")
        logger.info(f"Job ID: {job_id}")
        logger.info(f"Pipeline: {pipeline_name}")
        logger.info(f"Status: {result['status']}")
        logger.info(f"Time: {execution_time:.2f}s")

        return result

    except Exception as e:
        # ====================================================================
        # ERROR HANDLING
        # ====================================================================
        logger.error(f"\n{'='*80}")
        logger.error(f"❌ PIPELINE EXECUTION FAILED")
        logger.error(f"{'='*80}")
        logger.error(f"Job ID: {job_id}")
        logger.error(f"Pipeline: {pipeline_name}")
        logger.error(f"Error Type: {type(e).__name__}")
        logger.error(f"Error Message: {str(e)}", exc_info=True)

        # Prepare error result
        execution_time = (datetime.utcnow() - job_start_time).total_seconds()

        error_result = {
            "status": "failed",
            "pipeline_name": pipeline_name,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "execution_time": execution_time,
            "timestamp": job_start_time.isoformat()
        }

        # Store error in database
        try:
            error_msg = f"{type(e).__name__}: {str(e)}"
            db_manager.update_job_error(job_id, error_msg)
            logger.info(f"✅ Error logged to database")
        except Exception as log_error:
            logger.error(f"❌ Failed to log error: {log_error}")

        return error_result


@app.task(name='app.tasks.process_data')
def process_data(dataset_id: str, processing_type: str):
    """
    Process dataset (placeholder for additional tasks)
    """
    logger.info(f"Processing dataset {dataset_id} with type {processing_type}")
    return {
        "status": "completed",
        "dataset_id": dataset_id,
        "processing_type": processing_type
    }


@app.task(name='app.tasks.analyze_data')
def analyze_data(dataset_id: str, analysis_type: str):
    """
    Analyze dataset (placeholder for additional tasks)
    """
    logger.info(f"Analyzing dataset {dataset_id} with analysis {analysis_type}")
    return {
        "status": "completed",
        "dataset_id": dataset_id,
        "analysis_type": analysis_type
    }