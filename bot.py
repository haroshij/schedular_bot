import os
import asyncio
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
    CallbackContext,
    filters,
)

from keyboard import MAIN_MENU, task_actions, tasks_inline_menu
from states import ADD_DATE, ADD_TEXT, POSTPONE_DATE, SEARCH_QUERY, WEATHER_CITY
from database import init_db, add_task, get_nearest_task, get_all_tasks, update_task_time, mark_task_done, get_task_by_id, get_user_city, set_user_city
from utils import parse_datetime, format_task
from handlers.search import search_duckduckgo
from handlers.weather import get_weather

# --- Настройка таймзоны пользователя ---
USER_TZ = timezone(timedelta(hours=3))  # МСК, можно менять


# ---------------- START ----------------
async def start(update: Update, _: CallbackContext):
    await update.message.reply_text("Привет! Выбери действие 👇", reply_markup=MAIN_MENU)


# ---------------- ADD TASK ----------------
async def add_task_start(update: Update, _: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Введи дату и время:\nYYYY-MM-DD HH:MM")
    return ADD_DATE


async def add_task_date(update: Update, context: CallbackContext):
    dt = parse_datetime(update.message.text)
    if not dt:
        await update.message.reply_text("❌ Неверный формат. Попробуй ещё раз")
        return ADD_DATE

    # считаем, что пользователь ввёл время в своей локальной таймзоне
    dt_local = dt.replace(tzinfo=USER_TZ)
    dt_utc = dt_local.astimezone(timezone.utc)

    if dt_utc < datetime.now(timezone.utc):
        await update.message.reply_text("❌ Нельзя вводить прошедшую дату. Попробуй ещё раз")
        return ADD_DATE

    context.user_data["task_time"] = dt_utc
    await update.message.reply_text("Теперь введи текст задачи")
    return ADD_TEXT


async def add_task_text(update: Update, context: CallbackContext):
    await add_task(
        task_id=str(uuid4()),
        user_id=update.effective_user.id,
        title=update.message.text,
        scheduled_time=context.user_data["task_time"]
    )
    await update.message.reply_text("✅ Задача добавлена", reply_markup=MAIN_MENU)
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
    kb = task_actions(task["id"])
    if query:
        await query.edit_message_text(text, reply_markup=kb)
    else:
        await update.message.reply_text(text, reply_markup=kb)


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

    text = "Выберите задачу:"
    kb = tasks_inline_menu(tasks)

    if query:
        await query.edit_message_text(text, reply_markup=kb)
    else:
        await update.message.reply_text(text, reply_markup=kb)


# ---------------- CALLBACKS ----------------
async def callbacks(update: Update, context: CallbackContext):
    query = update.callback_query
    if not query:
        return None

    await query.answer()
    data = query.data

    # === МЕНЮ ===
    if data == "menu":
        await query.edit_message_text("Выбери действие 👇", reply_markup=MAIN_MENU)
        return None

    if data == "nearest_task":
        await nearest_task(update, context)
        return None

    if data == "all_tasks":
        await all_tasks(update, context)
        return None

    # === ЗАДАЧА ===
    if data.startswith("task:"):
        task_id = data.split(":", 1)[1]
        task = await get_task_by_id(task_id)
        if not task:
            await query.edit_message_text("❌ Задача не найдена", reply_markup=MAIN_MENU)
            return None
        await query.edit_message_text(format_task(task), reply_markup=task_actions(task_id))
        return None

    # === ДЕЙСТВИЯ С ЗАДАЧЕЙ ===
    if data.startswith(("done:", "postpone:")):
        action, task_id = data.split(":", 1)
        if action == "done":
            await mark_task_done(task_id)
            await all_tasks(update, context)
            return None
        elif action == "postpone":
            context.user_data["task_id"] = task_id
            await query.edit_message_text("Введи новую дату:\nYYYY-MM-DD HH:MM")
            return POSTPONE_DATE

    # === ПОИСК ===
    if data == "search":
        await query.edit_message_text("Введите запрос для поиска:")
        return SEARCH_QUERY

    # === ПОГОДА ===
    if data in ("weather", "weather_change"):
        user_id = update.effective_user.id
        if data == "weather_change":
            await query.edit_message_text("Введите новый город:")
            return WEATHER_CITY

        city = await get_user_city(user_id)
        if city:
            weather_data = await get_weather(city)
            if "error" in weather_data:
                text = f"Ошибка получения погоды для города {city}\n{weather_data['error']}"
            else:
                desc = weather_data["weather"][0]["description"]
                temp = weather_data["main"]["temp"]
                text = f"🌤 {city.title()}\n{desc.capitalize()}\n🌡 {round(temp)}°C"

            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("Выбрать другой город", callback_data="weather_change")],
                [InlineKeyboardButton("В меню", callback_data="menu")]
            ])
            await query.edit_message_text(text, reply_markup=kb)
            return None
        else:
            await query.edit_message_text("Введите город:")
            return WEATHER_CITY

    # === ДОБАВИТЬ ЗАДАЧУ ===
    if data == "add_task":
        await query.edit_message_text("Введи дату и время:\nYYYY-MM-DD HH:MM")
        return ADD_DATE

    return None


# ---------------- POSTPONE ----------------
async def postpone_date(update: Update, context: CallbackContext):
    dt = parse_datetime(update.message.text)
    if not dt:
        await update.message.reply_text("❌ Неверный формат. Попробуй ещё раз")
        return POSTPONE_DATE

    dt_local = dt.replace(tzinfo=USER_TZ)
    dt_utc = dt_local.astimezone(timezone.utc)

    if dt_utc < datetime.now(timezone.utc):
        await update.message.reply_text("❌ Нельзя вводить прошедшую дату. Попробуй ещё раз")
        return POSTPONE_DATE

    await update_task_time(context.user_data["task_id"], dt_utc)
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
        desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        text = f"🌤 {city.title()}\n{desc.capitalize()}\n🌡 {round(temp)}°C"

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔎Выбрать другой город", callback_data="weather_change")],
        [InlineKeyboardButton("↩️В меню", callback_data="menu")]
    ])

    await update.message.reply_text(text, reply_markup=kb)
    return ConversationHandler.END


# ---------------- MAIN ----------------
async def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("❌ TELEGRAM_TOKEN не найден!")

    app = ApplicationBuilder().token(token).build()

    # ---------- COMMANDS ----------
    app.add_handler(CommandHandler("start", start))

    # ---------- ADD TASK ----------
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(callbacks, pattern="^add_task$")],
        states={
            ADD_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_task_date)],
            ADD_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_task_text)]
        },
        fallbacks=[]
    ))

    # ---------- POSTPONE ----------
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(callbacks, pattern="^postpone:")],
        states={POSTPONE_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, postpone_date)]},
        fallbacks=[]
    ))

    # ---------- SEARCH ----------
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(callbacks, pattern="^search$")],
        states={SEARCH_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_query)]},
        fallbacks=[]
    ))

    # ---------- WEATHER ----------
    app.add_handler(ConversationHandler(
        entry_points=[
            CallbackQueryHandler(callbacks, pattern="^weather$"),
            CallbackQueryHandler(callbacks, pattern="^weather_change$")
        ],
        states={WEATHER_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, weather_city)]},
        fallbacks=[]
    ))

    # ---------- CALLBACKS ----------
    app.add_handler(CallbackQueryHandler(callbacks))

    # ---------- START POLLING ----------
    app.run_polling()

# ---------------- ENTRYPOINT ----------------
if __name__ == "__main__":
    load_dotenv()  # Подтягиваем .env локально и на сервере

    async def startup():
        await init_db()  # создаём таблицы в Postgres
        await main()

    try:
        asyncio.run(startup())
    except KeyboardInterrupt:
        print("Бот остановлен вручную")
    except Exception as e:
        print("❌ Ошибка при запуске бота:", e)
        raise
