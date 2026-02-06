from telegram import Update
from telegram.ext import CallbackContext

from handlers.common import cancel_menu_kb
from states import SEARCH_QUERY


async def handle_search_callbacks(update: Update, context: CallbackContext, data: str):
    query = update.callback_query

    if data == "search":
        await query.edit_message_text(
            "Введите запрос для поиска:",
            reply_markup=cancel_menu_kb()
        )
        return SEARCH_QUERY

    return None
