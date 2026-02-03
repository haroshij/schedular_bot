from telegram import InlineKeyboardMarkup, InlineKeyboardButton

# Главное меню
MAIN_MENU = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("➕ Добавить задачу", callback_data="add_task"),
        InlineKeyboardButton("⏭ Ближайшая задача", callback_data="nearest_task")
    ],
    [
        InlineKeyboardButton("📋 Все задачи", callback_data="all_tasks"),
        InlineKeyboardButton("🔍 Найти", callback_data="search")
    ],
    [
        InlineKeyboardButton("🌤 Текущая погода", callback_data="weather")
    ]
])

# Кнопки действий для отдельной задачи
def task_actions(task_id: str):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Выполнена", callback_data=f"done:{task_id}"),
            InlineKeyboardButton("⏳ Отложить", callback_data=f"postpone:{task_id}")
        ]
    ])
