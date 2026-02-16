from telegram import Update
from telegram.ext import CallbackContext
from services.search_service import search_duckduckgo
from handlers.common.common import cancel_menu_kb
from utils.search_utils import validate_search_query
from app.decorators import log_handler
from states import SEARCH_QUERY
from app.logger import logger


@log_handler
async def search_handler(update: Update, _: CallbackContext):
    """
    Обработчик ввода поискового запроса пользователем.

    Функция проверяет корректность запроса, выполняет поиск через
    DuckDuckGo и отправляет результаты пользователю. Если запрос
    некорректный, выводит предупреждение и оставляет пользователя
    в текущем состоянии для повторного ввода.

    Args:
        update (Update): Объект обновления Telegram с сообщением пользователя.
        _ (CallbackContext): Контекст, не используется в этой функции.

    Returns:
        str: Константа состояния SEARCH_QUERY для продолжения ввода запроса.
    """
    # Получаем текст запроса от пользователя
    query = update.message.text.strip()

    if not validate_search_query(query):
        await update.message.reply_text(
            "❌ Запрос некорректный. Попробуйте другой.",
            reply_markup=cancel_menu_kb(),
        )
        logger.info(
            "Пользователь %s ввёл некорректный запрос: %s",
            update.effective_user.id,
            query,
        )
        return SEARCH_QUERY  # Оставляем пользователя в состоянии ввода запроса

    # Выполняем поиск через DuckDuckGo
    results = await search_duckduckgo(query)

    # Формируем текст ответа из первых 5 результатов
    text = """Для повторного поиска отправьте новый запрос\n\n""" + "\n\n".join(results[:5])

    # Отправляем результаты пользователю
    await update.message.reply_text(
        text,
        reply_markup=cancel_menu_kb(),
    )

    return SEARCH_QUERY
