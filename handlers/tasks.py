from uuid import uuid4
from datetime import datetime, timezone, timedelta

from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

from database import (
    add_task,
    update_task_time,
    get_task_by_id,
)
from keyboard import MAIN_MENU
from utils import parse_datetime
from states import ADD_DATE, ADD_TEXT, POSTPONE_DATE
from bot.jobs import send_task_reminder

USER_TZ = timezone(timedelta(hours=3))


async def add_task_date(update: Update, context: CallbackContext):
    dt = parse_datetime(update.message.text)
    if not dt:
        await update.message.reply_text("❌ Неверный формат")
        return ADD_DATE

    dt_utc = dt.replace(tzinfo=USER_TZ).astimezone(timezone.utc)
    if dt_utc < datetime.now(timezone.utc):
        await update.message.reply_text("❌ Дата в прошлом")
        return ADD_DATE

    context.user_data["task_time"] = dt_utc
    await update.message.reply_text("Теперь введи текст задачи")
    return ADD_TEXT


async def add_task_text(update: Update, context: CallbackContext):
    task_id = str(uuid4())
    user_id = update.effective_user.id
    title = update.message.text
    scheduled_time = context.user_data["task_time"]

    await add_task(task_id, user_id, title, scheduled_time)
    task = await get_task_by_id(task_id)

    delay = (task["scheduled_time"] - datetime.now(timezone.utc)).total_seconds()
    context.application.job_queue.run_once(
        send_task_reminder,
        max(0, delay),
        data={"task_id": task_id, "chat_id": user_id},
        name=f"task_{task_id}",
    )

    await update.message.reply_text("✅ Задача добавлена", reply_markup=MAIN_MENU)
    context.user_data.clear()
    return ConversationHandler.END


async def postpone_date(update: Update, context: CallbackContext):
    dt = parse_datetime(update.message.text)
    if not dt:
        return POSTPONE_DATE

    dt_utc = dt.replace(tzinfo=USER_TZ).astimezone(timezone.utc)
    task_id = context.user_data["task_id"]

    await update_task_time(task_id, dt_utc)

    for job in context.application.job_queue.jobs():
        if job.name == f"task_{task_id}":
            job.schedule_removal()

    task = await get_task_by_id(task_id)
    delay = (task["scheduled_time"] - datetime.now(timezone.utc)).total_seconds()

    context.application.job_queue.run_once(
        send_task_reminder,
        max(0, delay),
        data={"task_id": task_id, "chat_id": task["user_id"]},
        name=f"task_{task_id}",
    )

    await update.message.reply_text("⏳ Время изменено", reply_markup=MAIN_MENU)
    return ConversationHandler.END
