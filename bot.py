from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from datetime import datetime, timedelta
import asyncio

from schedular import Scheduler
from task import Task
from storage import load_tasks, save_tasks
from utils import parse_time_interval, format_task

from keyboard import task_action_keyboard, postpone_keyboard
from utils import parse_time_interval

scheduler = Scheduler()


# ---------- Инициализация ----------
def load_from_storage():
    tasks = load_tasks()
    for task in tasks:
        scheduler.add_task(task)


def persist():
    tasks = [item[2] for item in scheduler.tasks_heap]
    save_tasks(tasks)


# ---------- Команды ----------
async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /add 10m Купить хлеб
    /add 1h Повторяющаяся задача
    """
    user_id = update.effective_user.id
    args = context.args

    if len(args) < 2:
        await update.message.reply_text(
            "Используй: /add <время (10m, 1h, 2d)> <текст>"
        )
        return

    try:
        delta = parse_time_interval(args[0])
    except ValueError as e:
        await update.message.reply_text(str(e))
        return

    title = " ".join(args[1:])
    scheduled_time = datetime.now() + delta

    task = Task(
        title=title,
        user_id=user_id,
        scheduled_time=scheduled_time
    )

    scheduler.add_task(task)
    persist()

    await update.message.reply_text(f"✅ Задача добавлена:\n{format_task(task)}")


async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    tasks = [item[2] for item in scheduler.tasks_heap if item[2].user_id == user_id]

    if not tasks:
        await update.message.reply_text("У тебя нет задач.")
        return

    tasks.sort(key=lambda t: t.scheduled_time)
    text = "\n\n".join(format_task(t) for t in tasks)
    await update.message.reply_text(text)


async def next_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    for _, _, task in scheduler.tasks_heap:
        if task.user_id == user_id:
            await update.message.reply_text(
                f"⏭ Следующая задача:\n{format_task(task)}"
            )
            return

    await update.message.reply_text("Нет ближайших задач.")


# ---------- Фоновый процесс ----------
async def task_notifier(app):
    while True:
        due_tasks = scheduler.check_due_tasks()

        for task in due_tasks:
            try:
                await app.bot.send_message(
                    chat_id=task.user_id,
                    text=f"⏰ Напоминание:\n{task.title}",
                    reply_markup=task_action_keyboard(task.id)
                )

                task.mark_completed()

                if not task.completed:  # повторяющаяся
                    scheduler.add_task(task)

                persist()

            except Exception as e:
                print("Ошибка уведомления:", e)

        await asyncio.sleep(5)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    action = parts[0]
    task_id = parts[1]

    task = scheduler.find_task_by_id(task_id)
    if not task:
        await query.edit_message_text("❌ Задача не найдена")
        return

    if action == "done":
        task.mark_completed()
        persist()
        await query.edit_message_text(f"✅ Задача выполнена:\n{task.title}")
        return

    if action == "postpone_menu":
        await query.edit_message_text(
            "На сколько отложить?",
            reply_markup=postpone_keyboard(task_id)
        )
        return

    if action == "postpone":
        delta = parse_time_interval(parts[2])
        task.postpone(delta)
        scheduler.add_task(task)
        persist()

        await query.edit_message_text(
            f"⏳ Задача отложена:\n{task.title}\nНовая дата: {task.scheduled_time}"
        )


# ---------- Main ----------
async def main():
    load_from_storage()

    app = ApplicationBuilder().token("YOUR_TELEGRAM_BOT_TOKEN").build()

    app.add_handler(CommandHandler("add", add_task))
    app.add_handler(CommandHandler("list", list_tasks))
    app.add_handler(CommandHandler("next", next_task))
    app.add_handler(CallbackQueryHandler(handle_callback))
    asyncio.create_task(task_notifier(app))

    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
