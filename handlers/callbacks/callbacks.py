from telegram import Update
from telegram.ext import CallbackContext

from handlers.callbacks.callbacks_menu import handle_menu_callbacks
from handlers.callbacks.callbacks_tasks import handle_tasks_callbacks
from handlers.callbacks.callbacks_weather import handle_weather_callbacks
from handlers.callbacks.callbacks_search import handle_search_callbacks
from app.decorators import log_handler
from app.logger import logger


@log_handler
async def callbacks(update: Update, context: CallbackContext):
    """
    Универсальный хендлер для всех callback-запросов Telegram.

    Функция последовательно передаёт callback-запросы в набор обработчиков:
    - Меню
    - Задачи
    - Погода
    - Поиск

    Args:
        update (Update): Объект обновления от Telegram.
        context (CallbackContext): Контекст выполнения хендлера.

    Returns:
        Any: Возвращает результат из первого обработчика, который что-то вернул,
             или None, если ни один обработчик не обработал callback.
    """

    # Получаем объект callback-запроса
    query = update.callback_query
    if not query:  # Если callback отсутствует — ничего не делаем
        logger.warning("Нет запроса в update!")
        return None

    # Отвечаем на callback, чтобы убрать "часы ожидания" в интерфейсе
    await query.answer()
    data = query.data

    for handler in (
        handle_menu_callbacks,
        handle_tasks_callbacks,
        handle_weather_callbacks,
        handle_search_callbacks,
    ):
        result = await handler(update, context, data)
        if result is not None:
            return result

    return None
