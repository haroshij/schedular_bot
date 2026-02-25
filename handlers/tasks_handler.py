from datetime import datetime, timezone
from telegram import Update
from telegram.ext import CallbackContext

from keyboard import MAIN_MENU
from states import ADD_DATE, ADD_TEXT, POSTPONE_DATE, END
from handlers.common.common import cancel_menu_kb
from services.tasks_service import create_task, change_task_time
from utils.tasks_utils import parse_and_validate_datetime
from app.decorators import log_handler
from app.logger import logger


@log_handler
async def add_task_date(update: Update, context: CallbackContext):
    dt_utc = parse_and_validate_datetime(update.message.text)
    if not dt_utc:
        await update.message.reply_text(
            "❌ Неверный формат или устаревшая дата. Попробуйте снова:\n\n"
            "Примеры:\n"
            "• 2026-02-10 18:30\n"
            "• сегодня 21:00\n"
            "• завтра 9:00",
            reply_markup=cancel_menu_kb(),
        )
        logger.info(
            "Пользователь %s ввёл неверный формат или устаревшую дату: %s",
            update.effective_user.id,
            update.message.text,
        )
        return ADD_DATE

    context.user_data["task_time"] = dt_utc
    await update.message.reply_text(
        "Теперь введи текст задачи:", reply_markup=cancel_menu_kb()
    )
    return ADD_TEXT


@log_handler
async def add_task_text(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    title = update.message.text
    scheduled_time = context.user_data["task_time"]

    now = datetime.now(timezone.utc)
    if scheduled_time < now:
        await update.message.reply_text(
            "❌ Введённая дата уже прошла. Задача не добавлена.",
            reply_markup=MAIN_MENU,
        )
        logger.info("Пользователь %s ввёл устаревшую дату: %s", user_id, scheduled_time)
        context.user_data.clear()
        return END

    task = await create_task(user_id, title, scheduled_time)
    delay = (task["scheduled_time"] - datetime.now(timezone.utc)).total_seconds()

    # Отправка Celery-задачи через строковую ссылку
    from bot.tasks import send_task_reminder_task
    send_task_reminder_task.apply_async(
        args=[task["id"], user_id, str(task["scheduled_time"])],
        countdown=max(0, delay),
    )

    await update.message.reply_text("✅ Задача добавлена", reply_markup=MAIN_MENU)
    context.user_data.clear()
    return END


@log_handler
async def postpone_date(update: Update, context: CallbackContext):
    dt_utc = parse_and_validate_datetime(update.message.text)
    if not dt_utc:
        await update.message.reply_text(
            "❌ Неверный формат или устаревшая дата. Попробуйте снова:\n\n"
            "Примеры:\n"
            "• 2026-02-10 18:30\n"
            "• сегодня 21:00\n"
            "• завтра 9:00",
            reply_markup=cancel_menu_kb(),
        )
        logger.warning(
            "Пользователь %s ввёл неверный формат или устаревшую дату: %s",
            update.effective_user.id,
            update.message.text,
        )
        return POSTPONE_DATE

    task_id = context.user_data["task_id"]
    task = await change_task_time(task_id, dt_utc)
    delay = (task["scheduled_time"] - datetime.now(timezone.utc)).total_seconds()

    from bot.tasks import send_task_reminder_task
    send_task_reminder_task.apply_async(
        args=[task_id, task["user_id"], str(task["scheduled_time"])],
        countdown=max(0, delay),
    )

    await update.message.reply_text("⏳ Время изменено", reply_markup=MAIN_MENU)
    return END