from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    CallbackContext,
    filters,
)

from uuid import uuid4

from keyboard import MAIN_MENU, task_actions
from states import (
    ADD_DATE,
    ADD_TEXT,
    POSTPONE_DATE,
    SEARCH_QUERY,
    WEATHER_CITY,
)
from database import (
    init_db,
    add_task,
    get_nearest_task,
    get_all_tasks,
    update_task_time,
    mark_task_done,
)
from utils import parse_datetime, format_task
from handlers.search import search_duckduckgo
from handlers.weather import get_weather


# ---------------- START ----------------
async def start(update: Update, _: CallbackContext):
    await update.message.reply_text(
        "Привет! Выбери действие 👇",
        reply_markup=MAIN_MENU
    )


# ---------------- ADD TASK ----------------
async def add_task_start(update: Update, _: CallbackContext):
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(
            "Введи дату и время в формате:\nYYYY-MM-DD HH:MM"
        )
    return ADD_DATE


async def add_task_date(update: Update, context: CallbackContext):
    dt = parse_datetime(update.message.text)
    if not dt:
        await update.message.reply_text("❌ Неверный формат. Попробуй ещё раз.")
        return ADD_DATE

    context.user_data["task_time"] = dt
    await update.message.reply_text("Теперь введи текст задачи")
    return ADD_TEXT


async def add_task_text(update: Update, context: CallbackContext):
    await add_task(
        task_id=str(uuid4()),
        user_id=update.effective_user.id,
        title=update.message.text,
        scheduled_time=context.user_data["task_time"],
    )

    await update.message.reply_text(
        "✅ Задача добавлена",
        reply_markup=MAIN_MENU
    )
    return ConversationHandler.END


# ---------------- NEAREST TASK ----------------
async def nearest_task(update: Update, _: CallbackContext):
    user_id = update.effective_user.id
    task = await get_nearest_task(user_id)

    query = update.callback_query

    if not task:
        text = "У тебя нет задач"
        if query:
            await query.edit_message_text(text, reply_markup=MAIN_MENU)
        else:
            await update.message.reply_text(text, reply_markup=MAIN_MENU)
        return

    text = format_task(task)

    if query:
        await query.edit_message_text(
            text,
            reply_markup=task_actions(task["id"])
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=task_actions(task["id"])
        )


# ---------------- ALL TASKS ----------------
async def all_tasks(update: Update, _: CallbackContext):
    tasks = await get_all_tasks(update.effective_user.id)
    query = update.callback_query

    if not tasks:
        text = "Список задач пуст"
        if query:
            await query.edit_message_text(text, reply_markup=MAIN_MENU)
        else:
            await update.message.reply_text(text, reply_markup=MAIN_MENU)
        return

    text = "\n\n".join(format_task(t) for t in tasks)

    if query:
        await query.edit_message_text(text, reply_markup=MAIN_MENU)
    else:
        await update.message.reply_text(text, reply_markup=MAIN_MENU)


# ---------------- CALLBACKS (INLINE BUTTONS) ----------------
async def callbacks(update: Update, context: CallbackContext):
    query = update.callback_query
    if not query:
        return None

    await query.answer()
    data = query.data

    # ---- КНОПКА "В МЕНЮ" ----
    if data == "menu":
        await query.edit_message_text(
            "Выбери действие 👇",
            reply_markup=MAIN_MENU
        )
        return None

    # ---- КНОПКИ ЗАДАЧ ----
    if ":" in data:
        action, task_id = data.split(":", 1)

        if action == "done":
            await mark_task_done(task_id)
            await query.edit_message_text(
                "✅ Задача выполнена",
                reply_markup=MAIN_MENU
            )

        elif action == "postpone":
            context.user_data["task_id"] = task_id
            await query.edit_message_text(
                "Введи новую дату:\nYYYY-MM-DD HH:MM"
            )
            return POSTPONE_DATE

        return None

    # ---- ГЛАВНОЕ INLINE-МЕНЮ ----
    if data == "nearest_task":
        await nearest_task(update, context)

    elif data == "add_task":
        return await add_task_start(update, context)

    elif data == "all_tasks":
        await all_tasks(update, context)

    elif data == "search":
        await query.edit_message_text("Введите запрос для поиска:")
        return SEARCH_QUERY

    elif data == "weather":
        await query.edit_message_text("Введите город:")
        return WEATHER_CITY

    return None


# ---------------- POSTPONE ----------------
async def postpone_date(update: Update, context: CallbackContext):
    dt = parse_datetime(update.message.text)
    if not dt:
        await update.message.reply_text("❌ Неверный формат")
        return POSTPONE_DATE

    await update_task_time(context.user_data["task_id"], dt)

    await update.message.reply_text(
        "⏳ Задача отложена",
        reply_markup=MAIN_MENU
    )
    return ConversationHandler.END


# ---------------- SEARCH ----------------
async def search_query(update: Update, _: CallbackContext):
    query_text = update.message.text
    results = await search_duckduckgo(query_text)

    await update.message.reply_text(
        "\n\n".join(results),
        reply_markup=MAIN_MENU
    )
    return ConversationHandler.END


# ---------------- WEATHER ----------------
async def weather_city(update: Update, _: CallbackContext):
    city = update.message.text.strip()
    data = await get_weather(city)

    if "error" in data:
        text = f"Ошибка получения погоды для города {city}\n{data['error']}"
    else:
        desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        text = f"🌤 {city.title()}\n{str(desc).capitalize()}\n🌡 {round(temp)}°C"

    await update.message.reply_text(text, reply_markup=MAIN_MENU)
    return ConversationHandler.END


# ---------------- MAIN ----------------
def main():
    app = ApplicationBuilder().token("7612875405:AAHzHyI3zX2P9KZUHNX-5gJdiM9dZItuX-c").build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(add_task_start, pattern="^add_task$")],
        states={
            ADD_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_task_date)],
            ADD_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_task_text)],
        },
        fallbacks=[]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(callbacks, pattern="^postpone:")],
        states={
            POSTPONE_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, postpone_date)]
        },
        fallbacks=[]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(callbacks, pattern="^search$")],
        states={
            SEARCH_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_query)]
        },
        fallbacks=[]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(callbacks, pattern="^weather$")],
        states={
            WEATHER_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, weather_city)]
        },
        fallbacks=[]
    ))

    app.add_handler(CallbackQueryHandler(callbacks, pattern="^(menu|nearest_task|all_tasks|add_task|search|weather)$"))

    print("🤖 Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    import asyncio

    asyncio.run(init_db())
    main()
