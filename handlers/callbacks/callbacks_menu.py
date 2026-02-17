from telegram import Update
from telegram.ext import CallbackContext
from keyboard import MAIN_MENU
from app.decorators import log_handler


@log_handler
async def handle_menu_callbacks(update: Update, _: CallbackContext, data: str):
    """
    Обрабатывает callback-запросы, связанные с главным меню.

    Args:
        update (Update): Объект обновления от Telegram.
        _ (CallbackContext): Контекст выполнения хендлера (не используется).
        data (str): Данные callback.

    Returns:
        None: Всегда возвращает None.
    """

    query = update.callback_query

    if data == "menu":
        await query.edit_message_text("Выбери действие 👇", reply_markup=MAIN_MENU)

    return None
