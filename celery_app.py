"""Celery Application Configuration"""
import os, logging
from celery import Celery
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

app = Celery('ml_platform')

app.conf.update(
    broker_url=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1'),
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    result_expires=3600,
    worker_max_tasks_per_child=100,
)

app.autodiscover_tasks(['app'])
logger.info(f"✅ Celery configured: {os.getenv('CELERY_BROKER_URL')}")