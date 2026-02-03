from telegram import Update
from telegram.ext import CallbackContext
from keyboard import MAIN_MENU

# Состояние для поиска
SEARCH_QUERY = 1001

async def menu_handler(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    message = update.effective_message

    from bot import nearest_task, all_tasks
    from handlers.weather import weather_handler

    if text == "⏭ Ближайшая задача":
        await nearest_task(update, context)

    elif text == "📋 Все задачи":
        await all_tasks(update, context)

    elif text == "🌤 Текущая погода":
        await weather_handler(update, context)

    elif text == "🔍 Найти":
        if message:
            await message.reply_text("Введите запрос для поиска:")
        return SEARCH_QUERY

    else:
        if message:
            await message.reply_text(
                "Выбери действие 👇",
                reply_markup=MAIN_MENU
            )

    return None
