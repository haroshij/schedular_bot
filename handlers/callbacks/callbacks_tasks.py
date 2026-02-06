from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

from keyboard import MAIN_MENU, task_actions, tasks_inline_menu
from handlers.common import cancel_menu_kb
from states import ADD_DATE, POSTPONE_DATE
from utils import format_task

from services.tasks_service import (
    get_task,
    get_tasks,
    get_nearest_user_task,
    complete_task,
)


async def handle_tasks_callbacks(update: Update, context: CallbackContext, data: str):
    query = update.callback_query
    user_id = update.effective_user.id

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
        task = await get_task(task_id)

        if not task or task["user_id"] != user_id:
            await query.edit_message_text(
                "❌ Эта задача не принадлежит вам",
                reply_markup=MAIN_MENU
            )
            return None

        context.user_data["task_id"] = task_id
        await query.edit_message_text(
            "Введите новую дату и время ⏰\n\n"
            "Примеры:\n"
            "• 2026-02-10 18:30\n"
            "• сегодня 21:00\n"
            "• завтра 9:00",
            reply_markup=cancel_menu_kb()
        )
        return POSTPONE_DATE

    # ---------- NEAREST TASK ----------
    if data == "nearest_task":
        task = await get_nearest_user_task(user_id)

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
        tasks = await get_tasks(user_id)

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
        task = await get_task(task_id)

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
        task = await get_task(task_id)

        if not task or task["user_id"] != user_id:
            await query.edit_message_text(
                "❌ Эта задача не принадлежит вам",
                reply_markup=MAIN_MENU
            )
            return None

        await complete_task(task_id)
        await query.edit_message_text(
            "✅ Задача выполнена",
            reply_markup=MAIN_MENU
        )
        return None

    return None
