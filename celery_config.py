"""
Celery Configuration - REDIS ONLY
"""

import os
from kombu import Exchange, Queue


class CeleryConfig:
    """Celery configuration class"""

    # Broker and Backend URLs - REDIS ONLY
    broker_url = os.getenv(
        'CELERY_BROKER_URL',
        'redis://localhost:6379/0'
    )

    result_backend = os.getenv(
        'CELERY_RESULT_BACKEND',
        'redis://localhost:6379/1'
    )

    # Task Serialization
    task_serializer = 'json'
    accept_content = ['json']
    result_serializer = 'json'

    # Timezone
    timezone = 'UTC'
    enable_utc = True

    # Task Execution Settings
    task_track_started = True
    task_time_limit = 30 * 60
    task_soft_time_limit = 25 * 60

    # Worker Settings
    worker_prefetch_multiplier = 1
    worker_max_tasks_per_child = 100

    # Queues
    default_exchange = Exchange('ml_platform', type='direct')
    ml_exchange = Exchange('ml_pipelines', type='direct')

    task_queues = (
        Queue('default', exchange=default_exchange, routing_key='default'),
        Queue('ml_pipelines', exchange=ml_exchange, routing_key='ml_pipelines'),
    )

    task_routes = {
        'app.tasks.execute_pipeline': {'queue': 'ml_pipelines'},
    }

    # Result Backend Settings
    result_expires = 86400
    result_extended = True

    # Logging
    worker_log_level = 'INFO'

    # Compatibility
    broker_connection_retry_on_startup = True
    broker_connection_retry = True