from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

from database import (
    get_nearest_task,
    get_all_tasks,
    get_task_by_id,
    mark_task_done,
    get_user_city,
)
from keyboard import MAIN_MENU, task_actions, tasks_inline_menu
from utils import format_task, translate_weather
from states import (
    ADD_DATE,
    POSTPONE_DATE,
    SEARCH_QUERY,
    WEATHER_CITY,
)
from handlers.weather import get_weather
from handlers.common import cancel_menu_kb


async def callbacks(update: Update, context: CallbackContext):
    query = update.callback_query
    if not query:
        return None

    await query.answer()
    data = query.data
    user_id = update.effective_user.id

    # ---------- MENU ----------
    if data == "menu":
        await query.edit_message_text(
            "Выбери действие 👇",
            reply_markup=MAIN_MENU
        )
        return None

    # ---------- ADD TASK ----------
    if data == "add_task":
        await query.edit_message_text(
            "Введите дату и время ⏰\n\n"
            "Примеры:\n"
            "• 2026-02-10 18:30\n"
            "• сегодня 21:00\n"
            "• завтра 9:00",
            reply_markup=cancel_menu_kb()
        )
        return ADD_DATE

    # ---------- POSTPONE ----------
    if data.startswith("postpone:"):
        task_id = data.split(":", 1)[1]
        task = await get_task_by_id(task_id)

        if not task or task["user_id"] != user_id:
            await query.edit_message_text(
                "❌ Эта задача не принадлежит вам",
                reply_markup=MAIN_MENU
            )
            return None

        context.user_data["task_id"] = task_id
        await query.edit_message_text(
            "Введите новую дату и время ⏰",
            reply_markup=cancel_menu_kb()
        )
        return POSTPONE_DATE

    # ---------- SEARCH ----------
    if data == "search":
        await query.edit_message_text(
            "Введите запрос для поиска:",
            reply_markup=cancel_menu_kb()
        )
        return SEARCH_QUERY

    # ---------- WEATHER ----------
    if data in ("weather", "weather_change"):
        city = await get_user_city(user_id)

        if city and data == "weather":
            weather_data = await get_weather(city)

            if "error" in weather_data:
                text = f"❌ {weather_data['error']}"
            else:
                desc_en = weather_data["weather"][0]["description"]
                desc = translate_weather(desc_en)
                temp = weather_data["main"]["temp"]
                text = (
                    f"🌤 {city.title()}\n"
                    f"{desc.capitalize()}\n"
                    f"🌡 {round(temp)}°C"
                )

            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Другой город", callback_data="weather_change")],
                [InlineKeyboardButton("↩️ В меню", callback_data="menu")]
            ])

            await query.edit_message_text(text, reply_markup=kb)
            return None

        await query.edit_message_text(
            "Введите город:",
            reply_markup=cancel_menu_kb()
        )
        return WEATHER_CITY

    # ---------- NEAREST TASK ----------
    if data == "nearest_task":
        task = await get_nearest_task(user_id)

        if task:
            await query.edit_message_text(
                format_task(task),
                reply_markup=task_actions(task["id"])
            )
        else:
            await query.edit_message_text(
                "Нет задач",
                reply_markup=MAIN_MENU
            )
        return None

    # ---------- ALL TASKS ----------
    if data == "all_tasks":
        tasks = await get_all_tasks(user_id)

        if tasks:
            kb = InlineKeyboardMarkup(
                tasks_inline_menu(tasks).inline_keyboard + (
                    (InlineKeyboardButton("↩️ В меню", callback_data="menu"),),
                )
            )
            await query.edit_message_text(
                "Выберите задачу:",
                reply_markup=kb
            )
        else:
            await query.edit_message_text(
                "Нет задач",
                reply_markup=MAIN_MENU
            )
        return None

    # ---------- SELECT TASK ----------
    if data.startswith("task:"):
        task_id = data.split(":", 1)[1]
        task = await get_task_by_id(task_id)

        if not task or task["user_id"] != user_id:
            await query.edit_message_text(
                "❌ Эта задача не принадлежит вам",
                reply_markup=MAIN_MENU
            )
            return None

        await query.edit_message_text(
            format_task(task),
            reply_markup=task_actions(task["id"])
        )
        return None

    # ---------- DONE ----------
    if data.startswith("done:"):
        task_id = data.split(":", 1)[1]
        task = await get_task_by_id(task_id)

        if not task or task["user_id"] != user_id:
            await query.edit_message_text(
                "❌ Эта задача не принадлежит вам",
                reply_markup=MAIN_MENU
            )
            return None

        await mark_task_done(task_id)
        await query.edit_message_text(
            "✅ Задача выполнена",
            reply_markup=MAIN_MENU
        )
        return None

    return None
