from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

from keyboard import MAIN_MENU, task_actions, tasks_inline_menu
from handlers.common.common import cancel_menu_kb
from states import ADD_DATE, POSTPONE_DATE
from utils.tasks_utils import format_task
from app.decorators import log_handler
from app.logger import logger
from services.tasks_service import (
    get_task,
    get_tasks,
    get_nearest_user_task,
    complete_task,
)


@log_handler
async def handle_tasks_callbacks(update: Update, context: CallbackContext, data: str):
    """
    Обрабатывает callback-запросы, связанные с задачами пользователя.
    Поддерживаются действия:
    - Добавление новой задачи (add_task)
    - Перенос даты задачи (postpone)
    - Просмотр ближайшей задачи (nearest_task)
    - Просмотр всех задач (all_tasks)
    - Просмотр конкретной задачи (task:<id>)
    - Отметка задачи как выполненной (done:<id>)

    Args:
        update (Update): Объект обновления от Telegram.
        context (CallbackContext): Контекст выполнения хендлера.
        data (str): Данные callback.

    Returns:
        str | None: Новое состояние ConversationHandler или None.
    """

    query = update.callback_query
    user_id = update.effective_user.id

    if data == "add_task":
        await query.edit_message_text(
            "Введите дату и время ⏰\n\n"
            "Примеры:\n"
            "• 2026-02-10 18:30\n"
            "• сегодня 21:00\n"
            "• завтра 9:00",
            reply_markup=cancel_menu_kb(),
        )
        logger.info("Пользователь %s пробует создать задачу", user_id)
        return ADD_DATE

    if data.startswith("postpone:"):
        task_id = data.split(":", 1)[1]
        task = await get_task(task_id)
        logger.info("Пользователь %s пробует перенести задачу %s", user_id, task_id)

        if not task or task["user_id"] != user_id:
            await query.edit_message_text(
                "❌ Эта задача не принадлежит вам", reply_markup=MAIN_MENU
            )
            logger.warning(
                "Пользователь %s попытался перенести не свою задачу %s",
                user_id,
                task_id,
            )
            return None

        context.user_data["task_id"] = task_id
        await query.edit_message_text(
            "Введите новую дату и время ⏰\n\n"
            "Примеры:\n"
            "• 2026-02-10 18:30\n"
            "• сегодня 21:00\n"
            "• завтра 9:00",
            reply_markup=cancel_menu_kb(),
        )
        return POSTPONE_DATE

    if data == "nearest_task":
        task = await get_nearest_user_task(user_id)
        logger.info(
            "Пользователь %s пробует получить информацию о ближайшей задаче", user_id
        )

        if task:
            await query.edit_message_text(
                format_task(task), reply_markup=task_actions(task["id"])
            )
            logger.info(
                "Пользователь %s получил информацию о ближайшей задаче %s",
                user_id,
                task["id"],
            )
        else:
            await query.edit_message_text("Нет задач", reply_markup=MAIN_MENU)
            logger.info(
                "Пользователь %s не получил информацию о ближайшей задаче, так как она отсутствует",
                user_id,
            )
        return None

    if data == "all_tasks":
        tasks = await get_tasks(user_id)
        logger.info("Пользователь %s пробует получить список всех задач", user_id)

        if tasks:
            kb = InlineKeyboardMarkup(
                tasks_inline_menu(tasks).inline_keyboard
                + ((InlineKeyboardButton("↩️ В меню", callback_data="menu"),),)
            )
            await query.edit_message_text("Выберите задачу:", reply_markup=kb)
            logger.info("Пользователь %s получил список всех задач", user_id)
        else:
            await query.edit_message_text("Нет задач", reply_markup=MAIN_MENU)
            logger.info(
                "Пользователь %s не получил список задач, так как задач нет", user_id
            )
        return None

    if data.startswith("task:"):
        task_id = data.split(":", 1)[1]
        task = await get_task(task_id)

        if not task or task["user_id"] != user_id:
            await query.edit_message_text(
                "❌ Эта задача не принадлежит вам", reply_markup=MAIN_MENU
            )
            logger.warning(
                "Пользователь %s попытался получить информацию о чужой задаче %s",
                user_id,
                task_id,
            )
            return None

        await query.edit_message_text(
            format_task(task), reply_markup=task_actions(task["id"])
        )
        logger.info("Пользователь %s получил информацию о задаче %s", user_id, task_id)
        return None

    if data.startswith("done:"):
        task_id = data.split(":", 1)[1]
        logger.info(
            "Пользователь %s пытается отметить задачу %s как выполненную",
            user_id,
            task_id,
        )
        task = await get_task(task_id)

        if not task or task["user_id"] != user_id:
            await query.edit_message_text(
                "❌ Эта задача не принадлежит вам", reply_markup=MAIN_MENU
            )
            logger.warning(
                "Пользователь %s попытался отметить не свою задачу %s как выполненную",
                user_id,
                task_id,
            )
            return None

        await complete_task(task_id)
        await query.edit_message_text("✅ Задача выполнена", reply_markup=MAIN_MENU)
        logger.info(
            "Пользователь %s отметил задачу %s как выполненную", user_id, task_id
        )
        return None

    return None
