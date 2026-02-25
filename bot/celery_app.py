import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from celery import Celery


REDIS_URL = os.getenv("REDIS_URL")

if not REDIS_URL:
    raise RuntimeError("REDIS_URL not set")


app = Celery(
    "bot_tasks",
    broker=f"{REDIS_URL}/1",
    backend=None,
    include=["bot.tasks"],
)


# базовая конфигурация Celery
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)