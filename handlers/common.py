from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

from keyboard import MAIN_MENU


async def start(update: Update, _: CallbackContext):
    await update.message.reply_text(
        "Привет! Выбери действие 👇",
        reply_markup=MAIN_MENU
    )


async def cancel(update: Update, context: CallbackContext):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "Действие отменено 👍\nВыбери действие 👇",
            reply_markup=MAIN_MENU
        )
    else:
        await update.message.reply_text(
            "Действие отменено 👍\nВыбери действие 👇",
            reply_markup=MAIN_MENU
        )

    context.user_data.clear()
    return ConversationHandler.END
