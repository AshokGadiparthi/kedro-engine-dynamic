#!/usr/bin/env python
"""
Kedro Pipeline Runner Wrapper
Handles parameter passing via JSON (solves CLI parsing issues)
Called from Celery tasks as subprocess

Usage:
    python run_pipeline.py <pipeline_name> [params_json]

Examples:
    python run_pipeline.py data_loading
    python run_pipeline.py feature_engineering '{"feature_engineering": {"n_features": 10}}'
"""

import sys
import json
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# IMPORTANT: These imports MUST work - if they fail, pipeline fails
# ============================================================================
try:
    from kedro.framework.project import configure_project
    from kedro.framework.session import KedroSession
    from kedro.framework.hooks import get_hook_manager
except ImportError as e:
    logger.error(f"❌ Kedro import failed: {e}")
    sys.exit(1)


def main():
    """Main entry point for pipeline execution"""

    # ========================================================================
    # Step 1: Parse command-line arguments
    # ========================================================================
    if len(sys.argv) < 2:
        logger.error("❌ Insufficient arguments")
        logger.info("Usage: python run_pipeline.py <pipeline_name> [params_json]")
        logger.info("Examples:")
        logger.info("  python run_pipeline.py data_loading")
        logger.info("  python run_pipeline.py feature_engineering '{\"feature_engineering\": {\"n_features\": 10}}'")
        sys.exit(1)

    pipeline_name = sys.argv[1]
    params_json = sys.argv[2] if len(sys.argv) > 2 else "{}"

    logger.info("=" * 80)
    logger.info("🚀 STARTING PIPELINE RUNNER WRAPPER")
    logger.info("=" * 80)
    logger.info(f"Pipeline: {pipeline_name}")

    try:
        # ====================================================================
        # Step 2: Parse parameters from JSON string
        # ====================================================================
        try:
            parameters = json.loads(params_json)
            logger.info(f"📊 Parameters loaded successfully")
            logger.info(f"   Total keys: {len(parameters)}")
            for key, value in parameters.items():
                logger.info(f"   - {key}: {type(value).__name__}")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON parameters: {e}")
            logger.error(f"   Received: {params_json[:100]}...")
            sys.exit(1)

        # ====================================================================
        # Step 3: Determine project path (script's parent directory)
        # ====================================================================
        project_path = Path(__file__).parent.absolute()
        logger.info(f"📂 Project path: {project_path}")

        # Verify project path exists
        if not project_path.exists():
            logger.error(f"❌ Project path does not exist: {project_path}")
            sys.exit(1)

        # Verify it's a Kedro project
        if not (project_path / "src" / "ml_engine" / "pipelines").exists():
            logger.warning(f"⚠️  Kedro pipelines directory not found in expected location")
            logger.warning(f"   Expected: {project_path}/src/ml_engine/pipelines")

        # ====================================================================
        # Step 4: Configure Kedro project
        # ====================================================================
        logger.info("🔧 Configuring Kedro project...")
        try:
            configure_project(str(project_path))
            logger.info("✅ Kedro project configured")
        except Exception as e:
            logger.error(f"❌ Failed to configure Kedro project: {e}")
            sys.exit(1)

        # ====================================================================
        # Step 5: Create KedroSession and execute pipeline
        # ====================================================================
        logger.info(f"🎯 Creating KedroSession...")

        with KedroSession.create(
                project_path=str(project_path),
                extra_params=parameters
        ) as session:
            logger.info(f"✅ KedroSession created")
            logger.info(f"📋 Running pipeline: {pipeline_name}")

            try:
                # Run the pipeline
                run_result = session.run(
                    pipeline_name=pipeline_name,
                    hook_manager=get_hook_manager()
                )

                logger.info("=" * 80)
                logger.info("✅ PIPELINE EXECUTION SUCCESSFUL")
                logger.info("=" * 80)

                # Return success
                sys.exit(0)

            except Exception as e:
                logger.error("=" * 80)
                logger.error("❌ PIPELINE EXECUTION FAILED")
                logger.error("=" * 80)
                logger.error(f"Error: {str(e)}", exc_info=True)
                sys.exit(1)

    except KeyboardInterrupt:
        logger.warning("⚠️  Pipeline interrupted by user")
        sys.exit(130)

    except Exception as e:
        logger.error("=" * 80)
        logger.error("❌ UNEXPECTED ERROR")
        logger.error("=" * 80)
        logger.error(f"Error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()