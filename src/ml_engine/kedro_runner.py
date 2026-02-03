"""
Kedro Execution Engine - No configure_project

Bypasses Kedro's configure_project to avoid package name issues
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import json
from datetime import datetime
import traceback
import sys
import os

# ============================================================================
# SETUP BEFORE ANY IMPORTS
# ============================================================================

os.environ['KEDRO_PACKAGE_NAME'] = 'ml_engine'

project_root = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

logger = logging.getLogger(__name__)

# ============================================================================
# Import Kedro WITHOUT configure_project
# ============================================================================

from kedro.framework.session import KedroSession
from kedro.runner import SequentialRunner

# ============================================================================
# EXCEPTION CLASSES
# ============================================================================


class KedroIntegrationError(Exception):
    """Base exception for Kedro integration errors"""
    pass


class PipelineNotFoundError(KedroIntegrationError):
    """Raised when requested pipeline doesn't exist"""
    pass


class PipelineExecutionError(KedroIntegrationError):
    """Raised when pipeline execution fails"""
    pass


# ============================================================================
# MAIN EXECUTOR CLASS
# ============================================================================


class KedroExecutor:
    """Execute and manage Kedro pipelines programmatically."""

    def __init__(self, project_path: str = None):
        """Initialize Kedro executor."""

        os.environ['KEDRO_PACKAGE_NAME'] = 'ml_engine'

        if project_path is None:
            project_path = str(project_root)
        else:
            project_path = str(Path(project_path).resolve())

        self.project_path = project_path

        if not Path(self.project_path).exists():
            raise FileNotFoundError(f"Project path not found: {self.project_path}")

        self._initialized = True
        self._context = None

        logger.info(f"KedroExecutor initialized: {self.project_path}")

    def initialize(self) -> bool:
        """Initialize Kedro project."""
        try:
            self._initialized = True
            logger.info("✅ Kedro project initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize: {e}")
            self._initialized = False
            return False

    def _ensure_initialized(self) -> None:
        """Verify executor is initialized."""
        if not self._initialized:
            raise KedroIntegrationError("Executor not initialized.")

    def get_available_pipelines(self) -> List[str]:
        """Get all available pipeline names."""
        self._ensure_initialized()

        try:
            os.environ['KEDRO_PACKAGE_NAME'] = 'ml_engine'

            with KedroSession.create(
                    project_path=self.project_path
            ) as session:
                context = session.load_context()
                pipeline_names = sorted(list(context.pipelines.keys()))
                logger.info(f"Found {len(pipeline_names)} pipelines")
                return pipeline_names
        except Exception as e:
            logger.error(f"Error retrieving pipelines: {e}")
            return []

    def get_pipeline_details(self, pipeline_name: str) -> Dict[str, Any]:
        """Get pipeline details."""
        self._ensure_initialized()

        try:
            os.environ['KEDRO_PACKAGE_NAME'] = 'ml_engine'

            with KedroSession.create(
                    project_path=self.project_path
            ) as session:
                context = session.load_context()

                if pipeline_name not in context.pipelines:
                    return {
                        "error": "Pipeline not found",
                        "available": list(context.pipelines.keys())
                    }

                pipeline = context.pipelines[pipeline_name]

                nodes = []
                for node in pipeline.nodes:
                    nodes.append({
                        "name": node.name,
                        "inputs": sorted(list(node.inputs)),
                        "outputs": sorted(list(node.outputs))
                    })

                return {
                    "name": pipeline_name,
                    "node_count": len(nodes),
                    "nodes": nodes
                }

        except Exception as e:
            logger.error(f"Error getting details: {e}")
            return {"error": str(e)}

    def get_pipeline_parameters(self, pipeline_name: str) -> Dict[str, Any]:
        """Get pipeline parameters."""
        self._ensure_initialized()

        try:
            os.environ['KEDRO_PACKAGE_NAME'] = 'ml_engine'

            with KedroSession.create(
                    project_path=self.project_path
            ) as session:
                context = session.load_context()

                if pipeline_name not in context.pipelines:
                    return {"error": f"Pipeline not found"}

                return dict(context.params)

        except Exception as e:
            logger.error(f"Error getting parameters: {e}")
            return {"error": str(e)}

    def execute_pipeline(
            self,
            pipeline_name: str,
            parameters: Optional[Dict[str, Any]] = None,
            tags: Optional[List[str]] = None,
            run_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a Kedro pipeline."""
        self._ensure_initialized()

        if not run_id:
            run_id = f"{pipeline_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        started_at = datetime.utcnow()

        try:
            logger.info(f"🚀 Starting pipeline: {pipeline_name}")
            logger.info(f"   Run ID: {run_id}")

            # CRITICAL: Set package name before creating session
            os.environ['KEDRO_PACKAGE_NAME'] = 'ml_engine'

            with KedroSession.create(
                    project_path=self.project_path
            ) as session:
                context = session.load_context()

                if pipeline_name not in context.pipelines:
                    return {
                        "status": "failed",
                        "error": f"Pipeline not found: {pipeline_name}"
                    }

                if parameters:
                    context.params.update(parameters)

                pipeline = context.pipelines[pipeline_name]

                if tags:
                    pipeline = pipeline.filter(*tags)
                    logger.info(f"Filtered to {len(pipeline.nodes)} nodes")

                logger.info(f"Executing {len(pipeline.nodes)} nodes...")

                runner = SequentialRunner()
                outputs = runner.run(
                    pipeline,
                    catalog=context.catalog,
                    hook_manager=context.hook_manager
                )

                completed_at = datetime.utcnow()
                execution_time = (completed_at - started_at).total_seconds()

                logger.info(f"✅ Pipeline completed in {execution_time:.2f}s")

                return {
                    "status": "success",
                    "pipeline_name": pipeline_name,
                    "run_id": run_id,
                    "outputs": self._serialize_outputs(outputs),
                    "node_count": len(pipeline.nodes),
                    "execution_time": round(execution_time, 2),
                    "started_at": started_at.isoformat(),
                    "completed_at": completed_at.isoformat()
                }

        except Exception as e:
            completed_at = datetime.utcnow()
            execution_time = (completed_at - started_at).total_seconds()

            logger.error(f"❌ Pipeline failed: {e}")
            logger.error(traceback.format_exc())

            return {
                "status": "failed",
                "pipeline_name": pipeline_name,
                "run_id": run_id,
                "error": str(e),
                "execution_time": round(execution_time, 2),
                "started_at": started_at.isoformat(),
                "completed_at": completed_at.isoformat()
            }

    @staticmethod
    def _serialize_outputs(outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize outputs to JSON-compatible format."""
        serialized = {}

        for key, value in outputs.items():
            try:
                json.dumps(value, default=str)
                serialized[key] = value
            except (TypeError, ValueError):
                serialized[key] = {
                    "_type": type(value).__name__,
                    "_value": str(value)[:500]
                }

        return serialized

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status."""
        try:
            pipelines = self.get_available_pipelines()
            return {
                "status": "healthy",
                "initialized": self._initialized,
                "project_path": str(self.project_path),
                "pipeline_count": len(pipelines),
                "pipelines": pipelines
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# ============================================================================
# SINGLETON EXECUTOR
# ============================================================================

_executor: Optional[KedroExecutor] = None


def get_executor(project_path: Optional[str] = None) -> KedroExecutor:
    """Get or create executor singleton."""
    global _executor

    os.environ['KEDRO_PACKAGE_NAME'] = 'ml_engine'

    if _executor is None:
        if project_path is None:
            project_path = str(project_root)

        _executor = KedroExecutor(project_path)
        _executor.initialize()

    return _executor

