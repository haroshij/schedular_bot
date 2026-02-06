from datetime import datetime, timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler

from keyboard import MAIN_MENU
from states import ADD_DATE, ADD_TEXT, POSTPONE_DATE
from bot.jobs import send_task_reminder
from services.tasks_service import create_task, change_task_time, parse_and_validate_datetime

# --- Клавиатура для кнопок "В меню" и "Отмена" ---
def cancel_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("↩️ В меню", callback_data="menu")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ])


# --- HANDLER: Ввод даты новой задачи ---
async def add_task_date(update: Update, context: CallbackContext):
    dt_utc = parse_and_validate_datetime(update.message.text)
    if not dt_utc:
        await update.message.reply_text(
            "❌ Неверный формат даты. Попробуйте снова:\n\n"
            "Примеры:\n"
            "• 2026-02-10 18:30\n"
            "• сегодня 21:00\n"
            "• завтра 9:00"
            ,
            reply_markup=cancel_menu_kb()
        )
        return ADD_DATE

    context.user_data["task_time"] = dt_utc
    await update.message.reply_text(
        "Теперь введи текст задачи:",
        reply_markup=cancel_menu_kb()
    )
    return ADD_TEXT


# --- HANDLER: Ввод текста новой задачи ---
async def add_task_text(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    title = update.message.text
    scheduled_time = context.user_data["task_time"]

    task = await create_task(user_id, title, scheduled_time)

    delay = (task["scheduled_time"] - datetime.now(timezone.utc)).total_seconds()
    context.application.job_queue.run_once(
        send_task_reminder,
        max(0, delay),
        data={"task": task, "chat_id": user_id},
        name=f"task_{task['id']}",
    )

    await update.message.reply_text("✅ Задача добавлена", reply_markup=MAIN_MENU)
    context.user_data.clear()
    return ConversationHandler.END


# --- HANDLER: Перенос задачи ---
async def postpone_date(update: Update, context: CallbackContext):
    dt_utc = parse_and_validate_datetime(update.message.text)
    if not dt_utc:
        await update.message.reply_text(
            "❌ Неверный формат даты. Попробуйте снова:",
            reply_markup=cancel_menu_kb()
        )
        return POSTPONE_DATE

    task_id = context.user_data["task_id"]
    task = await change_task_time(task_id, dt_utc)

    # Удаляем старое задание в job_queue
    for job in context.application.job_queue.jobs():
        if job.name == f"task_{task_id}":
            job.schedule_removal()

    delay = (task["scheduled_time"] - datetime.now(timezone.utc)).total_seconds()
    context.application.job_queue.run_once(
        send_task_reminder,
        max(0, delay),
        data={"task": task, "chat_id": task["user_id"]},
        name=f"task_{task_id}",
    )

    await update.message.reply_text("⏳ Время изменено", reply_markup=MAIN_MENU)
    return ConversationHandler.END
