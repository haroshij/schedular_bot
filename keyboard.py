from telegram import InlineKeyboardButton, InlineKeyboardMarkup

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
        kb.append([InlineKeyboardButton(t["title"], callback_data=f"task:{t['id']}")])
    return InlineKeyboardMarkup(kb)
