from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def task_action_keyboard(task_id: str):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Выполнил", callback_data=f"done:{task_id}"),
            InlineKeyboardButton("⏳ Отложить", callback_data=f"postpone_menu:{task_id}")
        ]
    ])


def postpone_keyboard(task_id: str):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("10 мин", callback_data=f"postpone:{task_id}:10m"),
            InlineKeyboardButton("1 час", callback_data=f"postpone:{task_id}:1h"),
        ],
        [
            InlineKeyboardButton("1 день", callback_data=f"postpone:{task_id}:1d"),
            InlineKeyboardButton("1 неделя", callback_data=f"postpone:{task_id}:1w"),
        ]
    ])
