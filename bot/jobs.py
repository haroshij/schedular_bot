from datetime import datetime, timezone
from telegram.ext import CallbackContext

from database import get_task_by_id, get_all_pending_tasks
from keyboard import task_actions
from utils.tasks_utils import format_task


async def send_task_reminder(context: CallbackContext):
    """Отправляет напоминание о задаче, только если она ещё pending."""
    job_data: dict | object = context.job.data  # говорим IDE, что это dict или object
    if not job_data:
        return

    task: dict = job_data["task"]
    chat_id: int = job_data["chat_id"]
    expected_time = task["scheduled_time"]

    # Получаем актуальные данные из БД
    task_db = await get_task_by_id(task["id"])
    if not task_db or task_db.get("status") != "pending" or task_db["scheduled_time"] != expected_time:
        # Задача выполнена или удалена — ничего не делаем
        return

    text = f"⏰ Напоминание!\n\n{format_task(task_db)}"

    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=task_actions(task_db["id"])
    )


async def restore_jobs(app):
    """Восстанавливаем все pending задачи при старте бота."""
    now = datetime.now(timezone.utc)
    tasks = await get_all_pending_tasks()

    for task in tasks:
        if task["scheduled_time"] <= now:
            continue

        job_name = f"task_{task['id']}"

        # Удаляем старые job’ы с таким именем
        old_jobs = app.job_queue.get_jobs_by_name(job_name)
        for job in old_jobs:
            job.schedule_removal()

        delay = (task["scheduled_time"] - now).total_seconds()

        # 🔑 Передаём в job полностью task + chat_id, чтобы send_task_reminder работал
        app.job_queue.run_once(
            send_task_reminder,
            delay,
            data={
                "task": task,
                "chat_id": task["user_id"],
            },
            name=job_name,
        )
