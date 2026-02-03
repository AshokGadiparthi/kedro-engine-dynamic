"""
Celery Application Instance
Separate file to avoid circular imports
"""

from celery import Celery
from celery_config import CeleryConfig

# Create Celery app
app = Celery("ml_platform")

# Load configuration
app.config_from_object(CeleryConfig)

print("✅ Celery app created and configured")
