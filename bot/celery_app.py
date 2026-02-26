"""
Celery configuration module.

Этот модуль создаёт и настраивает экземпляр Celery для обработки фоновых задач
(например, отправки напоминаний пользователям через Telegram).

Основные обязанности модуля:
- создание Celery-приложения
- настройка подключения к Redis (broker)
- регистрация задач
- базовая конфигурация worker'ов

Используется worker-процессами Celery.
"""

import os
import sys

# Добавляем корень проекта в PYTHONPATH.
# Это позволяет worker'у корректно импортировать модули проекта,
# когда Celery запускается отдельно от основного приложения.
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from celery import Celery

REDIS_URL = os.getenv("REDIS_URL")

if not REDIS_URL:
    raise RuntimeError("REDIS_URL not set")

# Создаём экземпляр Celery.
#
# Параметры:
# - "bot_tasks" — имя приложения (используется для логов и идентификации)
# - broker — Redis, через который передаются задачи
# - backend=None — результаты задач не сохраняются
# - include — список модулей с задачами Celery, которые нужно зарегистрировать
#
# Важно:
# broker=f"{REDIS_URL}/1" означает использование Redis database №1.
# Это позволяет изолировать очереди задач от других данных.
app = Celery(
    "bot_tasks",
    broker=f"{REDIS_URL}/1",
    backend=None,
    include=["bot.tasks"],
)

# базовая конфигурация Celery
app.conf.update(
    task_serializer="json",  # Формат сериализации задач при отправке в очередь.
    accept_content=["json"],  # Разрешённые форматы входящих задач.
    result_serializer="json",  # Формат сериализации результатов задач (надо указывать).
    timezone="UTC",
    enable_utc=True,  # Включает использование UTC во всех операциях Celery.
    task_acks_late=True,  # Подтверждение выполнения задачи только при успешном завершении.
    worker_prefetch_multiplier=1,  # Сколько задач worker может забрать заранее.
)
