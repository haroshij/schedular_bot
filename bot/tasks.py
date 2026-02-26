import os
import sys
import asyncio
from telegram import Bot

from bot.celery_app import app
from app.logger import logger
from database import get_task_by_id
from utils.tasks_utils import format_task
from keyboard import task_actions

# Добавляем корень проекта в PYTHONPATH.
# Это позволяет worker'у корректно импортировать модули проекта,
# когда Celery запускается отдельно от основного приложения.
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")


async def _send_task_reminder(task_id: str, chat_id: int, scheduled_time: str):
    """
    Полностью асинхронная логика отправки напоминания.

    Эта функция выполняет всю "реальную" работу задачи:
    - получает задачу из базы данных
    - проверяет её актуальность
    - формирует текст уведомления
    - отправляет сообщение пользователю через Telegram API

    Используется отдельная async-функция, потому что Celery-задачи
    по умолчанию синхронные, и для работы с async-кодом нужен
    синхронный wrapper (см. send_task_reminder_task).

    Args:
        task_id (str):
            Уникальный идентификатор задачи в базе данных.

        chat_id (int):
            Telegram chat_id пользователя, которому отправляется уведомление.

        scheduled_time (str):
            Время выполнения задачи в строковом виде.
            Используется как защита от гонок данных:
            если пользователь изменил время задачи после постановки
            Celery-задачи в очередь, уведомление не будет отправлено.
    """

    bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
    task_db = await get_task_by_id(task_id)

    if (
        not task_db
        or task_db.get("status") != "pending"
        or str(task_db["scheduled_time"]) != scheduled_time
    ):
        logger.info("Задача %s уже выполнена или удалена", task_id)
        return

    text = f"⏰ Напоминание!\n\n{format_task(task_db)}"
    logger.info("Отправляется напоминание задачи %s", task_id)

    await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=task_actions(task_id),
    )


@app.task
def send_task_reminder_task(task_id: str, chat_id: int, scheduled_time: str):
    """
    Celery-задача для отправки напоминания пользователю.

    Это синхронная "обёртка" над асинхронной функцией
    `_send_task_reminder`.

    Почему это нужно:
        - Celery по умолчанию выполняет задачи синхронно.
        - Основная логика проекта асинхронная (asyncpg, Telegram API).
        - Поэтому здесь создаётся или используется event loop,
          в котором запускается async-код.

    Алгоритм работы:
        1. Получаем текущий event loop worker'а.
        2. Если loop отсутствует — создаём новый.
        3. Запускаем async-функцию через run_until_complete().
        4. Логируем ошибки при сбоях.

    Args:
        task_id (str):
            Уникальный идентификатор задачи.

        chat_id (int):
            Telegram chat_id пользователя.

        scheduled_time (str):
            Запланированное время выполнения задачи.
            Используется для проверки актуальности задачи.

    Важно:
        - Каждая Celery-задача выполняется в отдельном worker-процессе.
        - Event loop создаётся на уровне процесса.
        - Ошибки не "роняют" worker, а логируются.
    """

    logger.info("Task запущена")

    try:
        # используем текущий loop Celery или создаём новый, если нет
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Запускаем асинхронную логику отправки уведомления и блокируем выполнение до её завершения.
        # Если не блокировать выполнение, Celery завершит задачу мгновенно,
        # async-код может не выполниться вообще или упасть без логов
        loop.run_until_complete(_send_task_reminder(task_id, chat_id, scheduled_time))

    except Exception as e:
        logger.exception(
            "Ошибка при отправке напоминания для задачи %s\n%s", task_id, e
        )
