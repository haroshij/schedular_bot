import os
import sys
import asyncio
from telegram import Bot

from bot.celery_app import app
from app.logger import logger
from database import get_task_by_id
from utils.tasks_utils import format_task
from keyboard import task_actions

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")


async def _send_task_reminder(task_id: str, chat_id: int, scheduled_time: str):
    """
    Полностью асинхронная логика отправки напоминания.
    """

    bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))

    # получаем задачу из БД
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
    Celery-задача (sync wrapper → async код).
    """

    logger.info("Task запушена")

    try:
        asyncio.run(_send_task_reminder(task_id, chat_id, scheduled_time))

    except Exception as e:
        logger.exception(
            "Ошибка при отправке напоминания для задачи %s\n%s", task_id, e
        )
