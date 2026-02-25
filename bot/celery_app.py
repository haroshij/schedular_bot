import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from celery import Celery
from celery.signals import worker_process_init
import asyncio
from database import init_db

REDIS_URL = os.getenv("REDIS_URL")

if not REDIS_URL:
    raise RuntimeError("REDIS_URL not set")


@worker_process_init.connect
def init_worker_db(**_):
    asyncio.run(init_db())


app = Celery(
    "bot_tasks",
    broker=REDIS_URL + "/1",
    backend=None,
    include=["bot.tasks"],
)