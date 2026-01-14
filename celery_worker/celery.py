import os
import django
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "giterview.settings")
django.setup()

app = Celery(include=["celery_worker.tasks"])

app.conf.update(
    {
        "broker_url": "amqp://rabbitmq:5672",
        "result_backend": "redis://redis:6379",
        "accept_content": ["json"],
        "task_serializer": "json",
        "result_serializer": "json",
        "task_time_limit": 64,
        "task_max_retries": 0,
        "result_expires": 3600,
        # "worker_pool": "threads",
    }
)
__all__ = ["app"]
