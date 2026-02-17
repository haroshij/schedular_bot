from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from utils.tasks_utils import format_task_date
from constants.keyboard_constants import MAX_TASK_LENGTH

MAIN_MENU = InlineKeyboardMarkup(  # Главное меню бота
    [
        [InlineKeyboardButton("➕ Добавить задачу", callback_data="add_task")],
        [InlineKeyboardButton("⏳ Ближайшая задача", callback_data="nearest_task")],
        [InlineKeyboardButton("📋 Все задачи", callback_data="all_tasks")],
        [InlineKeyboardButton("🔎 Поиск", callback_data="search")],
        [InlineKeyboardButton("🌤 Погода", callback_data="weather")],
    ]
)


def task_actions(task_id: str) -> InlineKeyboardMarkup:
    """
    Создает inline-клавиатуру с действиями для конкретной задачи.

    Args:
        task_id (str): Уникальный идентификатор задачи

    Returns:
        InlineKeyboardMarkup: Inline клавиатура с действиями для задачи
    """
    kb = [
        [InlineKeyboardButton("✅ Выполнена", callback_data=f"done:{task_id}")],
        [InlineKeyboardButton("⏰ Перенести", callback_data=f"postpone:{task_id}")],
        [InlineKeyboardButton("↩️ В меню", callback_data="menu")],
    ]
    return InlineKeyboardMarkup(kb)


def tasks_inline_menu(tasks: list) -> InlineKeyboardMarkup:
    """
    Создает inline-клавиатуру со списком всех задач пользователя.

    Args:
        tasks (list): Список словарей с задачами, где каждая задача
                      содержит как минимум поля 'id', 'title', 'scheduled_time'

    Returns:
        InlineKeyboardMarkup: Inline клавиатура со списком всех задач
    """
    kb = []
    for t in tasks:
        if len(t["title"]) > MAX_TASK_LENGTH:
            title = f"{t['title'][:MAX_TASK_LENGTH]}..."
        else:
            title = t["title"]
        text = f"{title}   ⏰ {format_task_date(t['scheduled_time'])}"
        kb.append([InlineKeyboardButton(text, callback_data=f"task:{t['id']}")])
    return InlineKeyboardMarkup(kb)


def weather_actions_kb() -> InlineKeyboardMarkup:
    """
    Создает inline-клавиатуру для действий в разделе погоды.

    Returns:
        InlineKeyboardMarkup: Inline клавиатура для действий с погодой
    """
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔄 Другой город", callback_data="weather_change")],
            [InlineKeyboardButton("↩️ В меню", callback_data="menu")],
        ]
    )
