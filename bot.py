import os
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    CallbackContext,
)

from database import (
    init_db,
    close_db,
    add_task,
    update_task_time,
    get_user_city,
    set_user_city,
    get_nearest_task,
    get_all_tasks,
    get_task_by_id,
    mark_task_done
)
from utils import parse_datetime, format_task, translate_weather
from handlers.search import search_duckduckgo
from handlers.weather import get_weather
from keyboard import MAIN_MENU, task_actions, tasks_inline_menu
from states import ADD_DATE, ADD_TEXT, POSTPONE_DATE, SEARCH_QUERY, WEATHER_CITY

USER_TZ = timezone(timedelta(hours=3))


# ---------------- REMINDERS ----------------
async def send_task_reminder(context: CallbackContext):
    """Отправляет напоминание о задаче, только если она ещё pending."""
    task: dict | object = context.job.data

    # Получаем актуальные данные из БД
    from database import get_task_by_id
    task_db = await get_task_by_id(task["id"])
    if not task_db or task_db.get("status") != "pending":
        # Задача выполнена или удалена — ничего не делаем
        return

    text = f"⏰ Напоминание!\n\n{format_task(task_db)}"

    await context.bot.send_message(
        chat_id=task_db["user_id"],
        text=text,
        reply_markup=task_actions(task_db["id"])
    )


async def restore_jobs(app):
    """Восстанавливает задачи при старте бота."""
    now = datetime.now(timezone.utc)

    # Берём только pending задачи с временем в будущем
    from database import get_all_pending_tasks
    tasks = await get_all_pending_tasks()
    tasks = [t for t in tasks if t.get("status") == "pending" and t["scheduled_time"] > now]

    for task in tasks:
        delay = (task["scheduled_time"] - now).total_seconds()
        app.job_queue.run_once(
            send_task_reminder,
            delay,
            data=task,
            name=f"task_{task['id']}"
        )


# ---------------- START ----------------
async def start(update: Update, _: CallbackContext):
    await update.message.reply_text("Привет! Выбери действие 👇", reply_markup=MAIN_MENU)


# ---------------- ADD TASK ----------------
async def add_task_date(update: Update, context: CallbackContext):
    dt = parse_datetime(update.message.text)
    if not dt:
        await update.message.reply_text(
            "❌ Неверный формат. Попробуйте ещё раз\n"
            "Примеры:\n• 2026-02-10 18:30\n"
            "• сегодня 21:00\n"
            "• завтра 9:00",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("❌ Отмена", callback_data="cancel")],
                 [InlineKeyboardButton("↩️ В меню", callback_data="menu")]])
        )
        return ADD_DATE

    dt_local = dt.replace(tzinfo=USER_TZ)
    dt_utc = dt_local.astimezone(timezone.utc)

    if dt_utc < datetime.now(timezone.utc):
        await update.message.reply_text(
            "❌ Нельзя вводить прошедшую дату. Попробуйте ещё раз\n"
            "Примеры:\n• 2026-02-10 18:30\n"
            "• сегодня 21:00\n"
            "• завтра 9:00",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("❌ Отмена", callback_data="cancel")],
                 [InlineKeyboardButton("↩️ В меню", callback_data="menu")]])
        )
        return ADD_DATE

    context.user_data["task_time"] = dt_utc
    await update.message.reply_text(
        "Теперь введи текст задачи",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Отмена", callback_data="cancel")],
             [InlineKeyboardButton("↩️ В меню", callback_data="menu")]])
    )
    return ADD_TEXT


async def add_task_text(update: Update, context: CallbackContext):
    task_id = str(uuid4())
    user_id = update.effective_user.id
    title = update.message.text
    scheduled_time = context.user_data["task_time"]

    # 1️⃣ Сохраняем задачу в БД
    await add_task(
        task_id=task_id,
        user_id=user_id,
        title=title,
        scheduled_time=scheduled_time
    )

    # 2️⃣ Получаем актуальные данные задачи из БД
    task = await get_task_by_id(task_id)

    if task and task.get("status") == "pending":
        # 3️⃣ Вычисляем задержку
        delay = (task["scheduled_time"] - datetime.now(timezone.utc)).total_seconds()
        if delay < 0:
            delay = 0

        # 4️⃣ Ставим job
        context.application.job_queue.run_once(
            send_task_reminder,
            delay,
            data=task,
            name=f"task_{task['id']}"
        )

    # 5️⃣ Сообщаем пользователю
    await update.message.reply_text("✅ Задача добавлена", reply_markup=MAIN_MENU)

    # 6️⃣ Чистим контекст
    context.user_data.clear()
    return ConversationHandler.END


# ---------------- POSTPONE ----------------
async def postpone_date(update: Update, context: CallbackContext):
    dt = parse_datetime(update.message.text)
    if not dt:
        await update.message.reply_text(
            "❌ Неверный формат. Попробуйте ещё раз\n"
            "Примеры:\n• 2026-02-10 18:30\n"
            "• сегодня 21:00\n"
            "• завтра 9:00",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("❌ Отмена", callback_data="cancel")],
                 [InlineKeyboardButton("↩️ В меню", callback_data="menu")]]),
        )
        return POSTPONE_DATE

    dt_local = dt.replace(tzinfo=USER_TZ)
    dt_utc = dt_local.astimezone(timezone.utc)

    if dt_utc < datetime.now(timezone.utc):
        await update.message.reply_text(
            "❌ Нельзя вводить прошедшую дату. Попробуйте ещё раз\n"
            "Примеры:\n• 2026-02-10 18:30\n"
            "• сегодня 21:00\n"
            "• завтра 9:00",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("❌ Отмена", callback_data="cancel")],
                 [InlineKeyboardButton("↩️ В меню", callback_data="menu")]]),
        )
        return POSTPONE_DATE

    task_id = context.user_data["task_id"]

    # ---------------- Обновляем время задачи в БД ----------------
    await update_task_time(task_id, dt_utc)

    # ---------------- Удаляем старый job ----------------
    for job in context.application.job_queue.jobs():
        if job.name == f"task_{task_id}":
            job.schedule_removal()

    # ---------------- Получаем актуальные данные задачи ----------------
    task = await get_task_by_id(task_id)

    # Проверяем статус задачи — только pending
    if task and task.get("status") == "pending":
        delay = (task["scheduled_time"] - datetime.now(timezone.utc)).total_seconds()
        if delay < 0:
            delay = 0

        context.application.job_queue.run_once(
            send_task_reminder,
            delay,
            data=task,
            name=f"task_{task['id']}"
        )

    await update.message.reply_text("⏳ Время изменено", reply_markup=MAIN_MENU)
    return ConversationHandler.END


# ---------------- SEARCH ----------------
async def search_query(update: Update, _: CallbackContext):
    query_text = update.message.text
    results = await search_duckduckgo(query_text)
    await update.message.reply_text("\n\n".join(results), reply_markup=MAIN_MENU)
    return ConversationHandler.END


# ---------------- WEATHER ----------------
async def weather_city(update: Update, _: CallbackContext):
    city = update.message.text.strip()
    await set_user_city(update.effective_user.id, city)
    data = await get_weather(city)

    if "error" in data:
        text = f"Ошибка получения погоды для города {city}\n{data['error']}"
    else:
        desc_en = data["weather"][0]["description"]
        desc = translate_weather(desc_en)
        temp = data["main"]["temp"]
        text = f"🌤 {city.title()}\n{desc.capitalize()}\n🌡 {round(temp)}°C"

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔎Выбрать другой город", callback_data="weather_change")],
        [InlineKeyboardButton("↩️В меню", callback_data="menu")]
    ])
    await update.message.reply_text(text, reply_markup=kb)
    return ConversationHandler.END


# ---------------- CALLBACKS ----------------
async def callbacks(update: Update, context: CallbackContext):
    query = update.callback_query
    if not query:
        return None

    await query.answer()
    data = query.data

    try:
        user_id = update.effective_user.id  # текущий пользователь

        # --- MENU ---
        if data == "menu":
            if getattr(query.message, "text", None) != "Выбери действие 👇":
                await query.edit_message_text("Выбери действие 👇", reply_markup=MAIN_MENU)
            return None

        # --- ADD TASK ---
        if data == "add_task":
            await query.edit_message_text(
                ("Введите дату и время ⏰\n\n"
                 "Примеры:\n• 2026-02-10 18:30\n"
                 "• сегодня 21:00\n"
                 "• завтра 9:00"),
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("❌ Отмена", callback_data="cancel")],
                     [InlineKeyboardButton("↩️ В меню", callback_data="menu")]
                     ])
            )
            return ADD_DATE

        if data.startswith("postpone:"):
            task_id = data.split(":", 1)[1]
            task = await get_task_by_id(task_id)
            if not task or task["user_id"] != user_id:
                await query.edit_message_text("❌ Эта задача не принадлежит вам", reply_markup=MAIN_MENU)
                return None
            context.user_data["task_id"] = task_id
            await query.edit_message_text(
                "Введите дату и время ⏰\n\n"
                "Примеры:\n• 2026-02-10 18:30\n"
                "• сегодня 21:00\n"
                "• завтра 9:00",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("❌ Отмена", callback_data="cancel")],
                     [InlineKeyboardButton("↩️ В меню", callback_data="menu")]]
                )
            )
            return POSTPONE_DATE

        # --- SEARCH ---
        if data == "search":
            await query.edit_message_text(
                "Введите запрос для поиска:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("↩️ В меню", callback_data="menu")]
                ])
            )
            return SEARCH_QUERY

        # --- WEATHER ---
        if data in ("weather", "weather_change"):
            city = await get_user_city(user_id) if data == "weather" else None
            if city:
                weather_data = await get_weather(city)
                if "error" in weather_data:
                    text = f"Ошибка получения погоды для города {city}\n{weather_data['error']}"
                else:
                    desc_en = weather_data["weather"][0]["description"]
                    desc = translate_weather(desc_en)
                    temp = weather_data["main"]["temp"]
                    text = f"🌤 {city.title()}\n{desc.capitalize()}\n🌡 {round(temp)}°C"

                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Выбрать другой город", callback_data="weather_change")],
                    [InlineKeyboardButton("↩️ В меню", callback_data="menu")]
                ])
                if getattr(query.message, "text", None) != text:
                    await query.edit_message_text(text, reply_markup=kb)
                return None
            else:
                await query.edit_message_text(
                    "Введите город:",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("↩️ В меню", callback_data="menu")]
                    ])
                )
                return WEATHER_CITY

        # --- NEAREST TASK ---
        if data == "nearest_task":
            task = await get_nearest_task(user_id)
            if task:
                text = format_task(task)
                kb = task_actions(task["id"])
            else:
                text = "Нет задач"
                kb = MAIN_MENU
            if getattr(query.message, "text", None) != text:
                await query.edit_message_text(text, reply_markup=kb)
            return None

        # --- MARK TASK DONE ---
        if data.startswith("done:"):
            task_id = data.split(":", 1)[1]
            task = await get_task_by_id(task_id)
            if not task or task["user_id"] != user_id:
                await query.edit_message_text("❌ Эта задача не принадлежит вам", reply_markup=MAIN_MENU)
                return None
            await mark_task_done(task_id)
            await query.edit_message_text("✅ Задача выполнена", reply_markup=MAIN_MENU)
            return None

        # --- ALL TASKS ---
        if data == "all_tasks":
            tasks = await get_all_tasks(user_id)
            if tasks:
                text = "Выберите задачу:"
                kb = tasks_inline_menu(tasks)
                new_keyboard = tuple(list(row) for row in kb.inline_keyboard)
                new_keyboard += (
                    (InlineKeyboardButton("↩️ В меню", callback_data="menu"),),
                )
                kb = InlineKeyboardMarkup(new_keyboard)
            else:
                text = "Нет задач"
                kb = MAIN_MENU
            if getattr(query.message, "text", None) != text:
                await query.edit_message_text(text, reply_markup=kb)
            return None

        # --- SELECT TASK FROM ALL ---
        if data.startswith("task:"):
            task_id = data.split(":", 1)[1]
            task = await get_task_by_id(task_id)
            if not task or task["user_id"] != user_id:
                await query.edit_message_text("❌ Эта задача не принадлежит вам", reply_markup=MAIN_MENU)
                return None
            text = format_task(task)
            kb = task_actions(task["id"])
            if getattr(query.message, "text", None) != text:
                await query.edit_message_text(text, reply_markup=kb)
            return None

    except Exception as e:
        print(f"Ошибка в callbacks: {e}")

    return None


# ---------------- MAIN ----------------
def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("❌ TELEGRAM_TOKEN не найден")

    async def on_startup(_):
        await init_db()
        await restore_jobs(app)

    async def on_shutdown(_):
        await close_db()

    app = (
        ApplicationBuilder()
        .token(token)
        .post_init(on_startup)
        .post_shutdown(on_shutdown)
        .build()
    )

    # COMMANDS
    app.add_handler(CommandHandler("start", start))

    # ---------------- CANCEL ----------------
    async def cancel(update: Update, context: CallbackContext):
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                "Действие отменено 👍\nВыбери действие 👇",
                reply_markup=MAIN_MENU
            )
        else:
            await update.message.reply_text(
                "Действие отменено 👍\nВыбери действие 👇",
                reply_markup=MAIN_MENU
            )

        context.user_data.clear()
        return ConversationHandler.END

    # ADD TASK
    app.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(callbacks, pattern="^add_task$")],
            states={
                ADD_DATE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, add_task_date),
                    CallbackQueryHandler(cancel, pattern="^cancel$")
                ],
                ADD_TEXT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, add_task_text),
                    CallbackQueryHandler(cancel, pattern="^cancel$")
                ],
            },
            fallbacks=[
                CommandHandler("cancel", cancel),
                CallbackQueryHandler(cancel, pattern="^menu$")
            ],
        )
    )

    # POSTPONE
    app.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(callbacks, pattern="^postpone:")],
            states={
                POSTPONE_DATE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, postpone_date),
                    CallbackQueryHandler(cancel, pattern="^cancel$")
                ]
            },
            fallbacks=[
                CallbackQueryHandler(cancel, pattern="^menu$")
            ],
        )
    )

    # SEARCH
    app.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(callbacks, pattern="^search$")],
            states={SEARCH_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_query)]},
            fallbacks=[],
        )
    )

    # WEATHER
    app.add_handler(
        ConversationHandler(
            entry_points=[
                CallbackQueryHandler(callbacks, pattern="^weather$"),
                CallbackQueryHandler(callbacks, pattern="^weather_change$"),
            ],
            states={WEATHER_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, weather_city)]},
            fallbacks=[],
        )
    )

    # CALLBACKS
    app.add_handler(CallbackQueryHandler(callbacks))

    # START BOT
    app.run_polling()


# ---------------- ENTRYPOINT ----------------
if __name__ == "__main__":
    load_dotenv()
    main()
