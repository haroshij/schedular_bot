"""
Модуль работы с задачами и напоминаниями.
Содержит функции для отправки напоминаний пользователям и восстановления всех
невыполненных задач при старте бота.
"""

from datetime import datetime, timezone
from telegram.ext import CallbackContext

from app.logger import logger
from bot.tasks import send_task_reminder_task
from database import get_task_by_id, get_all_pending_tasks
from keyboard import task_actions
from utils.tasks_utils import format_task


# НЕ ИСПОЛЬЗУЕТСЯ ПРИ ПЕРЕХОДЕ НА CELERY
async def send_task_reminder(context: CallbackContext):
    """Отправляет напоминание о задаче пользователю.

    Args:
        context (CallbackContext): Контекст callback job, содержит данные задачи.

    Raises:
        Exception: Логируется, если происходит ошибка при отправке сообщения.
    """
    # Получаем данные job (task + chat_id)
    job_data: dict | None = context.job.data
    if not job_data:
        logger.warning("Job без данных!")
        return

    task: dict = job_data["task"]
    chat_id: int = job_data["chat_id"]
    expected_time = task["scheduled_time"]

    try:
        task_db = await get_task_by_id(task["id"])
        if (
            not task_db
            or task_db.get("status") != "pending"
            or task_db["scheduled_time"] != expected_time
        ):
            logger.info("Задача %s уже выполнена или удалена", task["id"])
            return

        text = f"⏰ Напоминание!\n\n{format_task(task_db)}"

        await context.bot.send_message(
            chat_id=chat_id, text=text, reply_markup=task_actions(task_db["id"])
        )
        logger.info(
            "Напоминание отправлено пользователю %s для задачи %s", chat_id, task["id"]
        )
    except Exception as e:
        logger.error("Ошибка при отправке напоминания для задачи %s\n%s", task["id"], e)


async def restore_jobs(_):
    """
    Восстанавливает все pending задачи с Celery вместо job_queue.
    """

    logger.debug("Формирование напоминаний для всех невыполненных задач...")
    now = datetime.now(timezone.utc)
    tasks = await get_all_pending_tasks()

    for task in tasks:
        if task["scheduled_time"] <= now:
            continue

        delay = (task["scheduled_time"] - now).total_seconds()
        send_task_reminder_task.apply_async(
            args=[task["id"], task["user_id"], str(task["scheduled_time"])],
            countdown=max(0, delay)
        )
