"""Celery Worker Application"""

from celery import Celery
from celery_config import *

app = Celery("ml_platform")
app.config_from_object("celery_config")
app.autodiscover_tasks(["app.tasks"])

if __name__ == "__main__":
    app.start()
