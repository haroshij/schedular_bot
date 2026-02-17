import redis.asyncio as redis
import os
from app.logger import logger

REDIS_URL = os.getenv("REDIS_URL")

if not REDIS_URL:
    logger.warning("REDIS_URL не задан — cache отключён")
    redis_client = None
else:
    redis_client = redis.from_url(
        REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )


def get_redis_client():
    """
    Возвращает клиент Redis
    """

    return redis_client
