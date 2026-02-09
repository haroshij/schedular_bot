from functools import wraps
from app.logger import logger
from telegram.ext import CallbackContext, ConversationHandler
from telegram import Update

def log_handler(func):
    """
    Декоратор для логирования действий пользователя в асинхронных хендлерах.
    Логирует:
    - вход пользователя (user_id, текст или callback_data)
    - успешное завершение
    - ошибки с traceback
    """
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        user_id = None
        user_text = None
        callback_data = None

        try:
            # Получаем id пользователя
            if update.effective_user:
                user_id = update.effective_user.id

            # Входящие данные: текст или callback
            if update.message:
                user_text = update.message.text
            elif update.callback_query:
                callback_data = update.callback_query.data

            logger.info(
                "Пользователь %s вызвал %s | message: %s | callback: %s",
                user_id,
                func.__name__,
                user_text,
                callback_data
            )

            result = await func(update, context, *args, **kwargs)

            logger.debug(
                "Хендлер %s завершился успешно для пользователя %s",
                func.__name__,
                user_id
            )
            return result
        except Exception as e:
            logger.exception(
                "Ошибка в хендлере %s для пользователя %s\n%s",
                func.__name__,
                user_id,
                e
            )
            # Можно вернуть END, если это ConversationHandler

            return ConversationHandler.END
    return wrapper
