"""
Celery Tasks
Executes pipelines using external Kedro project
"""

import sys
import os
import json
import subprocess
from pathlib import Path
import logging
from datetime import datetime
from celery import Celery
import celery_config

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery('ml_platform')
celery_app.config_from_object(celery_config.CeleryConfig)

# EXTERNAL KEDRO PROJECT PATH - UPDATE THIS!
KEDRO_PROJECT_PATH = os.getenv(
    'KEDRO_PROJECT_PATH',
    '/home/ashok/work/latest/full/kedro-engine-dynamic'  # ← Change this to your Kedro project path
)

print(f"🔗 Kedro Project Path: {KEDRO_PROJECT_PATH}")


@celery_app.task(name='app.tasks.execute_pipeline', bind=True)
def execute_pipeline_task(self, job_id: str, pipeline_name: str, parameters: dict = None):
    """
    Execute a Kedro pipeline in external project
    
    Args:
        job_id: Unique job identifier
        pipeline_name: Name of pipeline to execute
        parameters: Pipeline parameters
    """
    
    logger.info(f"🚀 Starting pipeline execution: {pipeline_name} (Job: {job_id})")
    
    try:
        # Import database to update job status
        from app.core.job_manager import JobManager
        manager = JobManager()
        
        # Update job status to RUNNING
        manager.update_job_status(job_id, 'running')
        logger.info(f"✅ Job {job_id} status updated to RUNNING")
        
        # Call external Kedro project
        logger.info(f"📤 Calling external Kedro project at: {KEDRO_PROJECT_PATH}")
        
        result = execute_external_kedro_pipeline(
            kedro_path=KEDRO_PROJECT_PATH,
            pipeline_name=pipeline_name,
            parameters=parameters,
            run_id=job_id
        )
        
        # Update job with results
        if result['success']:
            manager.update_job_status(job_id, 'completed')
            manager.update_job_results(job_id, result['outputs'])
            logger.info(f"✅ Job {job_id} completed successfully")
            
            return {
                'status': 'success',
                'job_id': job_id,
                'pipeline_name': pipeline_name,
                'execution_time': result.get('execution_time', 0),
                'outputs': result.get('outputs', {})
            }
        else:
            manager.update_job_status(job_id, 'failed')
            manager.update_job_error(job_id, result.get('error', 'Unknown error'))
            logger.error(f"❌ Job {job_id} failed: {result.get('error')}")
            
            return {
                'status': 'failed',
                'job_id': job_id,
                'pipeline_name': pipeline_name,
                'error': result.get('error', 'Unknown error')
            }
    
    except Exception as e:
        logger.error(f"❌ Task execution failed: {e}", exc_info=True)
        
        # Update job status to FAILED
        try:
            from app.core.job_manager import JobManager
            manager = JobManager()
            manager.update_job_status(job_id, 'failed')
            manager.update_job_error(job_id, str(e))
        except Exception as db_error:
            logger.error(f"Failed to update job status: {db_error}")
        
        return {
            'status': 'failed',
            'job_id': job_id,
            'error': str(e)
        }


def execute_external_kedro_pipeline(
    kedro_path: str,
    pipeline_name: str,
    parameters: dict = None,
    run_id: str = None
) -> dict:
    """
    Execute a Kedro pipeline by calling the external project via CLI
    
    Args:
        kedro_path: Path to Kedro project
        pipeline_name: Pipeline name to execute
        parameters: Parameters dict
        run_id: Unique run identifier
    
    Returns:
        Dict with success status and results
    """
    
    try:
        # Verify Kedro project exists
        if not Path(kedro_path).exists():
            return {
                'success': False,
                'error': f'Kedro project not found at: {kedro_path}'
            }
        
        logger.info(f"📍 Kedro project verified at: {kedro_path}")
        
        # Build Kedro CLI command
        cmd = [
            'kedro', 'run',
            '--pipeline', pipeline_name,
        ]
        
        # Add parameters if provided
        if parameters:
            params_str = json.dumps(parameters)
            cmd.extend(['--params', params_str])
        
        logger.info(f"📋 Running command: {' '.join(cmd)}")
        logger.info(f"   Working directory: {kedro_path}")
        
        # Record start time
        start_time = datetime.utcnow()
        
        # Execute Kedro command
        result = subprocess.run(
            cmd,
            cwd=kedro_path,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout
        )
        
        # Record end time
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()
        
        # Check if execution was successful
        if result.returncode == 0:
            logger.info(f"✅ Pipeline executed successfully")
            logger.info(f"   Stdout: {result.stdout[:500]}")  # First 500 chars
            
            return {
                'success': True,
                'outputs': {
                    'message': 'Pipeline executed successfully',
                    'run_id': run_id
                },
                'execution_time': execution_time,
                'stdout': result.stdout
            }
        else:
            error_msg = result.stderr or result.stdout
            logger.error(f"❌ Pipeline execution failed")
            logger.error(f"   Return code: {result.returncode}")
            logger.error(f"   Error: {error_msg[:500]}")
            
            return {
                'success': False,
                'error': f'Kedro execution failed: {error_msg[:200]}',
                'execution_time': execution_time,
                'stderr': result.stderr,
                'stdout': result.stdout
            }
    
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Pipeline execution timed out (30 minutes)'
        }
    
    except Exception as e:
        logger.error(f"❌ Error executing external Kedro: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


@celery_app.task(name='app.tasks.check_pipeline', bind=True)
def check_pipeline_task(self, pipeline_name: str):
    """Check if a pipeline exists in Kedro project"""
    
    logger.info(f"🔍 Checking pipeline: {pipeline_name}")
    
    try:
        # Call Kedro CLI to list pipelines
        result = subprocess.run(
            ['kedro', 'pipeline', 'list'],
            cwd=KEDRO_PROJECT_PATH,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            pipelines = result.stdout.strip().split('\n')
            exists = pipeline_name in pipelines
            
            return {
                'pipeline_name': pipeline_name,
                'exists': exists,
                'available_pipelines': pipelines
            }
        else:
            return {
                'pipeline_name': pipeline_name,
                'exists': False,
                'error': result.stderr
            }
    
    except Exception as e:
        logger.error(f"Error checking pipeline: {e}")
        return {
            'pipeline_name': pipeline_name,
            'exists': False,
            'error': str(e)
        }


@celery_app.task(name='app.tasks.get_pipeline_info', bind=True)
def get_pipeline_info_task(self, pipeline_name: str):
    """Get information about a pipeline"""
    
    logger.info(f"ℹ️ Getting pipeline info: {pipeline_name}")
    
    return {
        'pipeline_name': pipeline_name,
        'message': 'Pipeline info endpoint'
    }
