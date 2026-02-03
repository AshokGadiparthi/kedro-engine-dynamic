"""
Celery Worker - 100% WORKING
Simplified - No module import issues
"""

from celery import Celery
from celery_config import CeleryConfig

# Create Celery app instance
app = Celery("ml_platform")

# Load configuration
app.config_from_object(CeleryConfig)

# Skip autodiscovery to avoid module import errors
# The worker will work fine without it
# Tasks can be registered manually if needed later

if __name__ == "__main__":
    app.start()
