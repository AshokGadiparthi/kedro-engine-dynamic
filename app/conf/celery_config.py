# Celery configuration
from kombu import Exchange, Queue

class CeleryConfig:
    """Celery configuration"""

    # Broker (message queue) - Redis
    broker_url = 'redis://localhost:6379/0'

    # Result backend - Redis
    result_backend = 'redis://localhost:6379/0'

    # Task settings
    task_serializer = 'json'
    accept_content = ['json']
    result_serializer = 'json'
    timezone = 'UTC'
    enable_utc = True

    # Task routes
    task_routes = {
        'app.tasks.execute_pipeline': {'queue': 'ml_pipelines'},
    }

    # Queues
    task_queues = (
        Queue('ml_pipelines', Exchange('ml_pipelines'), routing_key='ml_pipelines'),
    )

    # Worker settings
    worker_prefetch_multiplier = 1
    worker_max_tasks_per_child = 100