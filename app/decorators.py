from functools import wraps

from telegram.ext import CallbackContext
from telegram import Update

from app.logger import logger
from states import END


def log_handler(func):
    """
    Декоратор для логирования действий пользователя в хендлерах Telegram.

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
        user_id = None
        user_text = None
        callback_data = None

        try:
            if update.effective_user:
                user_id = update.effective_user.id
            if update.message:
                user_text = update.message.text
            elif update.callback_query:
                callback_data = update.callback_query.data

            logger.debug(
                "Пользователь %s вызвал %s | message: %s | callback: %s",
                user_id,
                func.__name__,
                user_text,
                callback_data,
            )

            result = await func(update, context, *args, **kwargs)

            logger.debug(
                "Хендлер %s завершился успешно для пользователя %s",
                func.__name__,
                user_id,
            )
            return result
        except Exception as e:
            logger.error(
                "Ошибка в хендлере %s для пользователя %s\n%s",
                func.__name__,
                user_id,
                e,
            )

            return END

    return wrapper
