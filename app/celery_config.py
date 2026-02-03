"""
Celery Configuration Module

COPY THIS ENTIRE FILE TO: celery_config.py
(Save in project root, same directory as main.py)

Location: ~/ml-platform/kedro-integrated-fast-api/celery_config.py
"""

import os
from kombu import Exchange, Queue

# ============================================================================
# BROKER & BACKEND CONFIGURATION
# ============================================================================

# Redis message broker URL
broker_url = os.getenv(
    'CELERY_BROKER_URL',
    'redis://localhost:6379/0'
)

# Redis result backend URL
result_backend = os.getenv(
    'CELERY_RESULT_BACKEND',
    'redis://localhost:6379/1'
)

# ============================================================================
# TASK SERIALIZATION
# ============================================================================

task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'

# ============================================================================
# TIMEZONE & TIME
# ============================================================================

timezone = 'UTC'
enable_utc = True

# ============================================================================
# TASK EXECUTION SETTINGS
# ============================================================================

task_track_started = True
task_time_limit = 30 * 60  # 30 minutes hard limit
task_soft_time_limit = 25 * 60  # 25 minutes soft limit

# ============================================================================
# WORKER SETTINGS
# ============================================================================

worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 100

# ============================================================================
# QUEUE CONFIGURATION
# ============================================================================

# Define exchanges
default_exchange = Exchange('ml_platform', type='direct')
ml_exchange = Exchange('ml_pipelines', type='direct')

# Define queues
task_queues = (
    Queue('default', exchange=default_exchange, routing_key='default'),
    Queue('ml_pipelines', exchange=ml_exchange, routing_key='ml_pipelines'),
)

# Task routing - send specific tasks to specific queues
task_routes = {
    'app.tasks.execute_pipeline_task': {'queue': 'ml_pipelines'},
    'app.tasks.check_pipeline': {'queue': 'default'},
    'app.tasks.get_pipeline_info': {'queue': 'default'},
}

# ============================================================================
# RESULT BACKEND SETTINGS
# ============================================================================

result_expires = 86400  # Results expire after 1 day
result_extended = True

# ============================================================================
# LOGGING
# ============================================================================

worker_log_level = 'INFO'

# ============================================================================
# COMPATIBILITY
# ============================================================================

broker_connection_retry_on_startup = True
broker_connection_retry = True