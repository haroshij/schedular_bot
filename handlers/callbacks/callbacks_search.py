from telegram import Update
from telegram.ext import CallbackContext
from handlers.common.common import cancel_menu_kb
from states import SEARCH_QUERY
from app.decorators import log_handler


@log_handler
async def handle_search_callbacks(update: Update, _: CallbackContext, data: str):
    """
    Обрабатывает callback-запросы, связанные с поиском задач.

    Если пользователь нажал кнопку "search":
        - редактирует сообщение с приглашением ввести запрос,
        - показывает клавиатуру отмены,
        - переводит пользователя в состояние SEARCH_QUERY.

    Args:
        update (Update): Объект обновления от Telegram.
        _ (CallbackContext): Контекст выполнения хендлера (не используется).
        data (str): Данные callback.

    Returns:
        str | None: Возвращает SEARCH_QUERY, если пользователь начал поиск,
                    иначе None.
    """

    query = update.callback_query  # Получаем объект callback

    if data == "search":
        # Редактируем сообщение с запросом ввода
        await query.edit_message_text(
            "Введите запрос для поиска:",
            reply_markup=cancel_menu_kb()
        )
        return SEARCH_QUERY

    # Если callback не относится к поиску — возвращаем None
    return None
