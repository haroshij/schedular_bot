from telegram import Update
from telegram.ext import CallbackContext

from keyboard import MAIN_MENU


async def handle_menu_callbacks(update: Update, _: CallbackContext, data: str):
    query = update.callback_query

    if data == "menu":
        await query.edit_message_text(
            "Выбери действие 👇",
            reply_markup=MAIN_MENU
        )
        return True

    return None
