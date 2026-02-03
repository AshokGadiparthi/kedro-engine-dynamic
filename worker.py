"""
Celery Worker Configuration
Sets up Celery to execute tasks
"""

import sys
import os
from pathlib import Path
from celery import Celery
import celery_config

# Get project root
project_root = Path(__file__).parent.resolve()
sys.path.insert(0, str(project_root))

# Create Celery app
app = Celery('ml_platform')

# Load configuration
app.config_from_object(celery_config.CeleryConfig)

# Autodiscover tasks from app
app.autodiscover_tasks(['app'])

@app.task(bind=True)
def debug_task(self):
    """Debug task"""
    print(f'Request: {self.request!r}')
    return 'Celery is working!'

if __name__ == '__main__':
    app.start()
