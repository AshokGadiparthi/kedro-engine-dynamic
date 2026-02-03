"""
Kedro Execution Engine for FastAPI Integration

This module provides programmatic access to Kedro pipelines,
enabling REST API exposure of ML workflows.

Features:
- Pipeline discovery and introspection
- Programmatic pipeline execution
- Parameter management
- Output capture and storage
- Error handling and logging
"""

from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
import json
from datetime import datetime
import traceback
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from kedro.framework.project import configure_project
from kedro.framework.session import KedroSession
from kedro.runner import SequentialRunner

logger = logging.getLogger(__name__)


class KedroIntegrationError(Exception):
    """Base exception for Kedro integration errors"""
    pass


class PipelineNotFoundError(KedroIntegrationError):
    """Raised when requested pipeline doesn't exist"""
    pass


class PipelineExecutionError(KedroIntegrationError):
    """Raised when pipeline execution fails"""
    pass


class KedroExecutor:
    """
    Execute and manage Kedro pipelines programmatically.
    
    This is the core integration point between FastAPI and Kedro,
    providing a clean interface for pipeline execution.
    """
    
    def __init__(self, project_path: str = "."):
        """
        Initialize Kedro executor.
        
        Args:
            project_path: Path to Kedro project root
            
        Raises:
            FileNotFoundError: If project path doesn't exist
        """
        self.project_path = Path(project_path).resolve()
        
        if not self.project_path.exists():
            raise FileNotFoundError(f"Project path not found: {self.project_path}")
        
        self._initialized = False
        self._context = None
        
        logger.info(f"KedroExecutor initialized with project: {self.project_path}")
    
    def initialize(self) -> bool:
        """
        Initialize Kedro project.
        
        Returns:
            True if successful
        """
        try:
            configure_project(self.project_path.as_posix())
            self._initialized = True
            logger.info("✅ Kedro project initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize Kedro project: {e}")
            return False
    
    def _ensure_initialized(self) -> None:
        """Verify executor is initialized."""
        if not self._initialized:
            raise KedroIntegrationError("Executor not initialized. Call initialize() first.")
    
    def get_available_pipelines(self) -> List[str]:
        """
        Get all available pipeline names.
        
        Returns:
            List of pipeline names
        """
        self._ensure_initialized()
        
        try:
            with KedroSession.create(
                project_path=self.project_path.as_posix()
            ) as session:
                context = session.load_context()
                pipeline_names = sorted(list(context.pipelines.keys()))
                logger.info(f"Found {len(pipeline_names)} pipelines: {pipeline_names}")
                return pipeline_names
        except Exception as e:
            logger.error(f"❌ Error retrieving pipelines: {e}")
            return []
    
    def get_pipeline_details(self, pipeline_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a pipeline.
        
        Args:
            pipeline_name: Name of the pipeline
            
        Returns:
            Dictionary containing pipeline details
        """
        self._ensure_initialized()
        
        try:
            with KedroSession.create(
                project_path=self.project_path.as_posix()
            ) as session:
                context = session.load_context()
                
                if pipeline_name not in context.pipelines:
                    available = list(context.pipelines.keys())
                    return {
                        "error": "Pipeline not found",
                        "requested": pipeline_name,
                        "available": available
                    }
                
                pipeline = context.pipelines[pipeline_name]
                
                # Extract node details
                nodes = []
                all_tags = set()
                
                for node in pipeline.nodes:
                    node_tags = list(node.tags) if node.tags else []
                    all_tags.update(node_tags)
                    
                    nodes.append({
                        "name": node.name,
                        "type": "task" if node._func else "data",
                        "function": node._func.__name__ if node._func else None,
                        "inputs": sorted(list(node.inputs)),
                        "outputs": sorted(list(node.outputs)),
                        "tags": node_tags
                    })
                
                return {
                    "name": pipeline_name,
                    "node_count": len(nodes),
                    "nodes": nodes,
                    "inputs": sorted(list(pipeline.inputs())),
                    "outputs": sorted(list(pipeline.outputs())),
                    "tags": sorted(list(all_tags))
                }
        
        except Exception as e:
            logger.error(f"❌ Error getting pipeline details: {e}")
            return {"error": str(e)}
    
    def get_pipeline_parameters(self, pipeline_name: str) -> Dict[str, Any]:
        """
        Get default parameters for a pipeline.
        
        Args:
            pipeline_name: Name of the pipeline
            
        Returns:
            Dictionary of parameters
        """
        self._ensure_initialized()
        
        try:
            with KedroSession.create(
                project_path=self.project_path.as_posix()
            ) as session:
                context = session.load_context()
                
                if pipeline_name not in context.pipelines:
                    return {"error": f"Pipeline '{pipeline_name}' not found"}
                
                return dict(context.params)
        
        except Exception as e:
            logger.error(f"❌ Error getting parameters: {e}")
            return {"error": str(e)}
    
    def execute_pipeline(
        self,
        pipeline_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        run_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a Kedro pipeline.
        
        Args:
            pipeline_name: Name of pipeline to execute
            parameters: Override parameters
            tags: Node tags to execute
            run_id: Unique identifier for this run
            
        Returns:
            Dictionary with execution results
        """
        self._ensure_initialized()
        
        if not run_id:
            run_id = f"{pipeline_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        started_at = datetime.utcnow()
        
        try:
            logger.info(f"🚀 Starting pipeline execution: {pipeline_name}")
            logger.info(f"   Run ID: {run_id}")
            
            with KedroSession.create(
                project_path=self.project_path.as_posix()
                #save_on_exit=False
            ) as session:
                context = session.load_context()
                
                # Verify pipeline exists
                if pipeline_name not in context.pipelines:
                    return {
                        "status": "failed",
                        "error": f"Pipeline '{pipeline_name}' not found"
                    }
                
                # Merge parameters
                if parameters:
                    context.params.update(parameters)
                
                # Get pipeline
                pipeline = context.pipelines[pipeline_name]
                
                # Filter by tags if specified
                if tags:
                    pipeline = pipeline.filter(*tags)
                    logger.info(f"Filtered pipeline to {len(pipeline.nodes)} nodes")
                
                # Create runner
                runner = SequentialRunner()
                
                # Execute pipeline
                logger.info(f"Executing {len(pipeline.nodes)} nodes...")
                
                outputs = runner.run(
                    pipeline,
                    catalog=context.catalog,
                    hook_manager=context.hook_manager
                )
                
                completed_at = datetime.utcnow()
                execution_time = (completed_at - started_at).total_seconds()
                
                logger.info(f"✅ Pipeline executed successfully")
                logger.info(f"   Execution time: {execution_time:.2f}s")
                
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
            
            error_trace = traceback.format_exc()
            logger.error(f"❌ Pipeline execution failed: {e}")
            logger.error(f"Traceback:\n{error_trace}")
            
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
        """
        Serialize pipeline outputs to JSON-compatible format.
        
        Args:
            outputs: Raw pipeline outputs
            
        Returns:
            JSON-serializable dictionary
        """
        serialized = {}
        
        for key, value in outputs.items():
            try:
                json.dumps(value, default=str)
                serialized[key] = value
            except (TypeError, ValueError):
                serialized[key] = {
                    "_type": type(value).__name__,
                    "_value": str(value)[:500]  # Limit to 500 chars
                }
        
        return serialized
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of Kedro integration.
        
        Returns:
            Dictionary with health information
        """
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


# Singleton instance
_executor: Optional[KedroExecutor] = None


def get_executor(project_path: str = ".") -> KedroExecutor:
    """Get or create Kedro executor singleton."""
    global _executor
    
    if _executor is None:
        _executor = KedroExecutor(project_path)
        _executor.initialize()
    
    return _executor
