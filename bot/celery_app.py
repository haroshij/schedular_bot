import sys
import os
from celery import Celery

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

REDIS_URL = os.getenv("REDIS_URL")

app = Celery(
    "bot_tasks",
    broker=REDIS_URL + "/1",
    backend=None,
    include=["bot.tasks"]  # <- это важно, чтобы Celery точно видел твой tasks.py
)

# Worker автоматически найдёт задачи в папке bot
app.autodiscover_tasks(["bot"])
