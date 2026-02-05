from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from utils import format_task_date

# Главное меню
MAIN_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("➕ Добавить задачу", callback_data="add_task")],
    [InlineKeyboardButton("⏳ Ближайшая задача", callback_data="nearest_task")],
    [InlineKeyboardButton("📋 Все задачи", callback_data="all_tasks")],
    [InlineKeyboardButton("🔎 Поиск", callback_data="search")],
    [InlineKeyboardButton("🌤 Погода", callback_data="weather")]
])


# Кнопки для конкретной задачи
def task_actions(task_id: str) -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton("✅ Выполнена", callback_data=f"done:{task_id}")],
        [InlineKeyboardButton("⏰ Перенести", callback_data=f"postpone:{task_id}")],
        [InlineKeyboardButton("↩️ В меню", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(kb)


# Список всех задач
def tasks_inline_menu(tasks: list) -> InlineKeyboardMarkup:
    kb = []
    for t in tasks:
        if len(t['title']) > 19:
            title = f"{t['title'][:15]}..."
        else:
            title = t['title']
        text = f"  {title}   ⏰ {format_task_date(t['scheduled_time'])}  "
        kb.append([InlineKeyboardButton(text, callback_data=f"task:{t['id']}")])
    return InlineKeyboardMarkup(kb)
