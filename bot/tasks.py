import os, sys
from telegram import Bot
from bot.celery_app import app
from app.logger import logger
from database import get_task_by_id
from utils.tasks_utils import format_task
from keyboard import task_actions

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")


@app.task  # Celery регистрирует функцию как удалённую задачу
def send_task_reminder_task(task_id: str, chat_id: int, scheduled_time: str):
    """
    Celery-задача для отправки напоминания.
    """

    logger.info('Task запушена')
    bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))  # Синхронный бот для worker

    try:
        task_db = get_task_by_id(task_id)  # Важно: используем синхронный вызов или await run_sync
        if hasattr(task_db, "__await__"):  # Если get_task_by_id асинхронная
            import asyncio
            task_db = asyncio.run(task_db)

        if (
                not task_db
                or task_db.get("status") != "pending"
                or str(task_db["scheduled_time"]) != scheduled_time  # Защита от race condition
        ):
            logger.info("Задача %s уже выполнена или удалена", task_id)
            return

        text = f"⏰ Напоминание!\n\n{format_task(task_db)}"
        logger.info("Отправляется напоминание задачи %s", task_id)
        bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=task_actions(task_id)
        )

    except Exception as e:
        logger.exception(
            "Ошибка при отправке напоминания для задачи %s\n%s", task_id, e
        )
