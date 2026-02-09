from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler
from keyboard import MAIN_MENU
from app.logger import logger
from app.decorators import log_handler

def cancel_menu_kb():
    """Возвращает клавиатуру с кнопками 'В меню' и 'Отмена'"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("↩️ В меню", callback_data="menu")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ])


@log_handler
async def start(update: Update, _: CallbackContext):
    await update.message.reply_text(
        "Привет! Выбери действие 👇",
        reply_markup=MAIN_MENU
    )


@log_handler
async def cancel(update: Update, context: CallbackContext):
    """
    Отмена действия: очищаем user_data и показываем главное меню.
    Работает как для callback_query, так и для обычных сообщений.
    """
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

    # Очистка временных данных пользователя
    logger.info('Удалены временные данные пользователя %s', update.effective_user.id)
    context.user_data.clear()
    return ConversationHandler.END
