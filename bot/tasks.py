import os
import asyncio
from telegram import Bot
from bot.celery_app import app
from app.logger import logger
from database import get_task_by_id
from utils.tasks_utils import format_task
from keyboard import task_actions

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=TELEGRAM_TOKEN)


@app.task
def send_task_reminder_task(task_id: str, chat_id: int, scheduled_time: str):
    """
    Celery задача для отправки напоминания.
    Проверяет, что задача ещё актуальна перед отправкой.
    """

    async def _send():
        try:
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
            await bot.send_message(chat_id=chat_id, text=text, reply_markup=task_actions(task_id))
        except Exception as e:
            logger.exception("Ошибка при отправке напоминания для задачи %s\n%s", task_id, e)

    asyncio.run(_send())
