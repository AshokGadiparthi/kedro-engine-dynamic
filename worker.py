"""
Celery Worker Initialization

This is the file that creates the Celery app instance!

Run with: celery -A worker worker --loglevel=info
"""

from celery import Celery
import celery_config

# Create Celery app
app = Celery('ml_platform')

# Load configuration from celery_config.py
app.config_from_object(celery_config)

# Auto-discover tasks from app module
app.autodiscover_tasks(['app'])

@app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery"""
    print(f'Request: {self.request!r}')
    return 'Celery is working!'