"""Celery Configuration - 100% WORKING"""

import os


class CeleryConfig:
    """Celery configuration class"""
    
    # Broker and backend
    broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
    
    # Serialization
    task_serializer = "json"
    accept_content = ["json"]
    result_serializer = "json"
    
    # Timezone
    timezone = "UTC"
    enable_utc = True
    
    # Task settings
    task_time_limit = 30 * 60  # 30 minutes
    task_soft_time_limit = 25 * 60  # 25 minutes
