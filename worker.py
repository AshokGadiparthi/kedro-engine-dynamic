"""Celery Worker - Explicit Task Import"""

import sys
import os
from pathlib import Path

# ============================================================================
# CRITICAL: Add paths FIRST
# ============================================================================

worker_dir = Path(__file__).parent.resolve()
project_root = worker_dir

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

os.environ['KEDRO_PACKAGE_NAME'] = 'ml_engine'

print(f"✅ Project root: {project_root}")
print(f"✅ sys.path[0]: {sys.path[0]}")

# ============================================================================
# Create Celery app
# ============================================================================

from celery import Celery
import celery_config

app = Celery('ml_platform')
app.config_from_object(celery_config.CeleryConfig)

print("✅ Celery app created")

# ============================================================================
# EXPLICITLY IMPORT TASKS (instead of autodiscovery)
# ============================================================================

try:
    from app import tasks
    print("✅ Tasks imported successfully!")
    print(f"   Available tasks: {list(app.tasks.keys())}")
except ImportError as e:
    print(f"❌ Failed to import tasks: {e}")
    print(f"   Trying to list app directory...")
    app_path = project_root / "app"
    if app_path.exists():
        print(f"   app/ directory exists at: {app_path}")
        print(f"   Contents: {list(app_path.iterdir())}")
    else:
        print(f"   ❌ app/ directory does NOT exist!")

# ============================================================================
# Debug task
# ============================================================================

@app.task(bind=True)
def debug_task(self):
    """Debug task"""
    return 'Celery is working!'

if __name__ == '__main__':
    app.start()