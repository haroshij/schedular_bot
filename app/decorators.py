from functools import wraps
from app.logger import logger
from telegram.ext import CallbackContext, ConversationHandler
from telegram import Update


def log_handler(func):
    """
    Декоратор для логирования действий пользователя в асинхронных хендлерах Telegram.

    Логирует следующие события:
    - Вход пользователя в хендлер (user_id, текст сообщения или callback_data)
    - Успешное завершение хендлера
    - Исключения с полным traceback

    Args:
        func (Callable): Асинхронная функция-хендлер, которую оборачиваем

    Returns:
        Callable: Обёрнутая функция с логированием
    """

    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        """
        Обёртка для хендлера. Выполняет логирование и обработку ошибок.

        Args:
            update (Update): Объект обновления Telegram
            context (CallbackContext): Контекст хендлера
            *args: Дополнительные позиционные аргументы
            **kwargs: Дополнительные именованные аргументы

        Returns:
            Любое значение, возвращаемое оригинальным хендлером, либо ConversationHandler.END при ошибке
        """
        user_id = None  # id пользователя
        user_text = None  # текст сообщения пользователя
        callback_data = None  # данные callback кнопки

        try:
            # Получаем id пользователя, если он есть
            if update.effective_user:
                user_id = update.effective_user.id

            # Получаем текст сообщения или данные callback, если они есть
            if update.message:
                user_text = update.message.text
            elif update.callback_query:
                callback_data = update.callback_query.data

            # Логируем вход пользователя в хендлер
            logger.info(
                "Пользователь %s вызвал %s | message: %s | callback: %s",
                user_id,
                func.__name__,
                user_text,
                callback_data
            )

            # Выполняем сам хендлер
            result = await func(update, context, *args, **kwargs)

            # Логируем успешное завершение хендлера
            logger.debug(
                "Хендлер %s завершился успешно для пользователя %s",
                func.__name__,
                user_id
            )
            return result
        except Exception as e:
            # Логируем любую ошибку с полным traceback
            logger.exception(
                "Ошибка в хендлере %s для пользователя %s\n%s",
                func.__name__,
                user_id,
                e
            )

            # Возвращаем ConversationHandler.END, чтобы корректно завершить разговор при ошибке
            return ConversationHandler.END

    return wrapper
