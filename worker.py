"""Celery Worker Initialization"""

import sys
import os
from pathlib import Path

# CRITICAL: Set up paths FIRST, before any other imports
project_root = Path(__file__).parent.resolve()
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

os.environ['KEDRO_PACKAGE_NAME'] = 'ml_engine'

# NOW create Celery app
from celery import Celery
import celery_config

# Create Celery app
app = Celery('ml_platform')

# Load configuration
app.config_from_object(celery_config.CeleryConfig)

# Auto-discover tasks (this will work now that paths are set)
app.autodiscover_tasks(['app'])

@app.task(bind=True)
def debug_task(self):
    """Debug task"""
    print(f'Request: {self.request!r}')
    return 'Celery is working!'

if __name__ == '__main__':
    app.start()