from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from keyboard import MAIN_MENU
from app.logger import logger
from app.decorators import log_handler
from states import END


def cancel_menu_kb():
    """
    Создаёт и возвращает клавиатуру с кнопкой "Отмена".
    Эта клавиатура используется для всех состояний, где пользователь
    может отменить текущее действие или вернуться в главное меню.

    Returns:
        InlineKeyboardMarkup: Объект клавиатуры Telegram.
    """
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel")],
        ]
    )


@log_handler
async def start(update: Update, _: CallbackContext):
    """
    Обработчик команды /start.
    Отправляет приветственное сообщение пользователю и выводит главное меню.

    Args:
        update (Update): Объект обновления Telegram.
        _ (CallbackContext): Контекст, не используется.
    """
    await update.message.reply_text(
        "Привет! Выбери действие 👇", reply_markup=MAIN_MENU
    )


@log_handler
async def cancel(update: Update, context: CallbackContext):
    """
    Отмена текущего действия.
    Функция очищает временные данные пользователя (user_data) и
    возвращает его в главное меню.

    Args:
        update (Update): Объект обновления Telegram.
        context (CallbackContext): Контекст с данными пользователя.

    Returns:
        int: ConversationHandler.END для завершения разговорного хендлера.
    """
    # Если действие вызвано через callback кнопку
    if update.callback_query:
        await update.callback_query.answer()  # Отвечаем на callback
        await update.callback_query.edit_message_text(
            "Действие отменено 👍\nВыбери действие 👇", reply_markup=MAIN_MENU
        )
    else:
        # Если действие вызвано обычным сообщением (ПОКА НЕ ИСПОЛЬЗУЕТСЯ)
        await update.message.reply_text(
            "Действие отменено 👍\nВыбери действие 👇", reply_markup=MAIN_MENU
        )

    # Очищаем временные данные пользователя
    logger.info("Удалены временные данные пользователя %s", update.effective_user.id)
    context.user_data.clear()
    return END
