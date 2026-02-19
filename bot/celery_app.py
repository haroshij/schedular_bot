import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL")

app = Celery(
    "bot_tasks",
    broker=REDIS_URL + "/1",
    backend=REDIS_URL + "/2"  # ??? Можно поставить None?
)