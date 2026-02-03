"""
Celery Configuration
Simple configuration pointing to Redis
"""

class CeleryConfig:
    """Celery configuration"""
    
    # Broker settings
    broker_url = 'redis://localhost:6379/0'
    result_backend = 'redis://localhost:6379/1'
    
    # Task settings
    task_serializer = 'json'
    accept_content = ['json']
    result_serializer = 'json'
    timezone = 'UTC'
    enable_utc = True
    
    # Task execution
    task_track_started = True
    task_time_limit = 30 * 60  # 30 minutes hard limit
    task_soft_time_limit = 25 * 60  # 25 minutes soft limit
    
    # Worker settings
    worker_prefetch_multiplier = 4
    worker_max_tasks_per_child = 1000
