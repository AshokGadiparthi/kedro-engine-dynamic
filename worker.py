"""Celery Worker - Set paths BEFORE any imports"""

import sys
import os
from pathlib import Path

# ============================================================================
# CRITICAL: Add project root to sys.path FIRST
# ============================================================================

# Get the directory where THIS file is located
worker_dir = Path(__file__).parent.resolve()
project_root = worker_dir  # worker.py is in project root

# Add project root to Python path
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

print(f"Worker starting from: {worker_dir}")
print(f"Project root: {project_root}")
print(f"sys.path[0]: {sys.path[0]}")

os.environ['KEDRO_PACKAGE_NAME'] = 'ml_engine'

# ============================================================================
# NOW import Celery (after paths are set)
# ============================================================================

from celery import Celery
import celery_config

print("✅ Imports successful")

# Create Celery app
app = Celery('ml_platform')

# Load configuration
app.config_from_object(celery_config.CeleryConfig)

print("✅ Celery config loaded")

# Auto-discover tasks - THIS WILL NOW WORK
print("🔍 Autodiscovering tasks from 'app' package...")
app.autodiscover_tasks(['app'])

print("✅ Tasks discovered")

@app.task(bind=True)
def debug_task(self):
    """Debug task"""
    print(f'Request: {self.request!r}')
    return 'Celery is working!'

if __name__ == '__main__':
    app.start()