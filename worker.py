"""Celery Worker Application"""

from celery import Celery
from celery_config import CeleryConfig

app = Celery("ml_platform")
app.config_from_object(CeleryConfig)
app.autodiscover_tasks(["app"])

if __name__ == "__main__":
    app.start()
