import sys
import os
from typing import Optional

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from celery import Celery
from celery.signals import worker_process_init
import asyncio
from database import init_db

REDIS_URL = os.getenv("REDIS_URL")

if not REDIS_URL:
    raise RuntimeError("REDIS_URL not set")

# глобальный loop для worker process
worker_loop: Optional[asyncio.AbstractEventLoop] = None


def get_worker_loop() -> asyncio.AbstractEventLoop:
    if worker_loop is None:
        raise RuntimeError("Worker loop not initialized")
    return worker_loop


@worker_process_init.connect
def init_worker_db(**_):
    global worker_loop
    worker_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(worker_loop)
    worker_loop.run_until_complete(init_db())


app = Celery(
    "bot_tasks",
    broker=REDIS_URL + "/1",
    backend=None,
    include=["bot.tasks"],
)
