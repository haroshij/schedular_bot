import os
from celery import Celery
import bot.tasks

REDIS_URL = os.getenv("REDIS_URL")

# Создаётся Celery instance
# Это центральный объект:
# - регистрирует задачи
# - знает broker
# - знает worker
# - управляет очередью
app = Celery(
    "bot_tasks",
    # Брокер будет на БД №1. Celery будет хранить там:
    # - задачи
    # - параметры
    # - отсчёт времени
    # - статус выполнения
    broker=REDIS_URL + "/1",
    backend=None,  # Результаты задач сохранять, поэтому здесь None
)
# Говорим worker'у, где искать задачи
app.autodiscover_tasks(["bot"])
