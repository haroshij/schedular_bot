from telegram import Update
from telegram.ext import CallbackContext
from keyboard import MAIN_MENU
from app.decorators import log_handler


@log_handler
async def handle_menu_callbacks(update: Update, _: CallbackContext, data: str):
    """
    Обрабатывает callback-запросы, связанные с главным меню.

    Если пользователь нажал кнопку "menu", редактирует сообщение и
    показывает главное меню.

    Args:
        update (Update): Объект обновления от Telegram.
        _ (CallbackContext): Контекст выполнения хендлера (не используется).
        data (str): Данные callback.

    Returns:
        None: Всегда возвращает None.
    """

    query = update.callback_query  # Получаем объект callback

    # Проверяем, что пользователь нажал кнопку "menu"
    if data == "menu":
        # Редактируем сообщение и выводим главное меню
        await query.edit_message_text(
            "Выбери действие 👇",
            reply_markup=MAIN_MENU
        )
        return None

    # Если callback не относится к меню — возвращаем None
    return None
