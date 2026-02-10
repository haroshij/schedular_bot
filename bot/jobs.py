from datetime import datetime, timezone
from telegram.ext import CallbackContext

from app.logger import logger
from database import get_task_by_id, get_all_pending_tasks
from keyboard import task_actions
from utils.tasks_utils import format_task

"""
Модуль работы с задачами и напоминаниями.

Содержит функции для отправки напоминаний пользователям и восстановления всех 
невыполненных задач при старте бота.
"""


async def send_task_reminder(context: CallbackContext):
    """Отправляет напоминание о задаче пользователю.

    Проверяет наличие данных в job, статус задачи в БД и совпадение времени.
    Если задача всё ещё pending, формирует текст и клавиатуру и отправляет сообщение.

    Args:
        context (CallbackContext): Контекст callback job, содержит данные задачи.

    Raises:
        Exception: Логируется, если происходит ошибка при отправке сообщения.
    """
    # Получаем данные job (task + chat_id)
    job_data: dict | object = context.job.data  # говорим IDE, что это dict или object
    if not job_data:
        logger.warning("Job без данных!")
        return

    task: dict = job_data["task"]
    chat_id: int = job_data["chat_id"]
    expected_time = task["scheduled_time"]

    # Получаем актуальные данные задачи из БД
    try:
        task_db = await get_task_by_id(task["id"])
        # Проверка статуса задачи и времени выполнения
        if (
            not task_db
            or task_db.get("status") != "pending"
            or task_db["scheduled_time"] != expected_time
        ):
            logger.info("Задача %s уже выполнена или удалена", task["id"])
            return

        # Формируем текст напоминания
        text = f"⏰ Напоминание!\n\n{format_task(task_db)}"

        # Отправляем сообщение пользователю с кнопками действий
        await context.bot.send_message(
            chat_id=chat_id, text=text, reply_markup=task_actions(task_db["id"])
        )
        logger.info(
            "Напоминание отправлено пользователю %s для задачи %s", chat_id, task["id"]
        )
    except Exception as e:
        # Логируем исключение, чтобы не потерять ошибку
        logger.exception(
            "Ошибка при отправке напоминания для задачи %s\n%s", task["id"], e
        )


async def restore_jobs(app):
    """Восстанавливает все pending задачи при старте бота.

    Для каждой задачи:
        1. Проверяет, что время задачи ещё не прошло.
        2. Удаляет старые job'ы с таким же именем.
        3. Вычисляет задержку до времени выполнения задачи.
        4. Планирует новую job в job_queue с передачей task + chat_id.

    Args:
        app (telegram.ext.Application): Экземпляр Application бота, содержит job_queue.
    """
    logger.debug("Формирование напоминаний для всех невыполненных задач...")
    now = datetime.now(timezone.utc)  # текущее UTC время
    tasks = await get_all_pending_tasks()  # получаем все pending задачи из БД

    for task in tasks:
        # Пропускаем задачи, которые уже должны были сработать
        if task["scheduled_time"] <= now:
            continue

        # Формируем уникальное имя job
        job_name = f"task_{task['id']}"

        # Удаляем старые job’ы с таким именем, чтобы не было дубликатов
        old_jobs = app.job_queue.get_jobs_by_name(job_name)
        for job in old_jobs:
            job.schedule_removal()

        # Вычисляем задержку до срабатывания задачи
        delay = (task["scheduled_time"] - now).total_seconds()

        # Планируем новую job для отправки напоминания
        # Передаём в job полностью task + chat_id, чтобы send_task_reminder работал
        app.job_queue.run_once(
            send_task_reminder,
            delay,
            data={
                "task": task,
                "chat_id": task["user_id"],
            },
            name=job_name,
        )
