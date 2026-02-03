"""Celery Worker"""

import sys
import os
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.resolve()
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

os.environ['KEDRO_PACKAGE_NAME'] = 'ml_engine'

from celery import Celery
import celery_config

# Create app
app = Celery('ml_platform')
app.config_from_object(celery_config.CeleryConfig)

# Autodiscover tasks
app.autodiscover_tasks(['app'])

@app.task(bind=True)
def debug_task(self):
    return 'Celery is working!'

if __name__ == '__main__':
    app.start()