from telegram import Update
from telegram.ext import CallbackContext

from keyboard import weather_actions_kb
from services.weather_service import get_weather_with_translation
from database import set_user_city
from states import END
from app.decorators import log_handler
from app.logger import logger


@log_handler
async def weather_handler(update: Update, _: CallbackContext):
    """
    Обрабатывает ввод города пользователем для получения прогноза погоды.
    Функция получает название города из сообщения пользователя,
    запрашивает прогноз через сервис погоды с переводом описания,
    отправляет результат пользователю и сохраняет город в базе.
    В случае ошибки (город не найден или сервис недоступен) выводит
    сообщение об ошибке.

    Args:
        update (Update): Объект обновления Telegram с сообщением пользователя.
        _ (CallbackContext): Контекст Telegram (не используется в этой функции).

    Returns:
        str: ConversationHandler.END — завершение текущего разговора.
    """

    city = update.message.text.strip()
    user_id = update.effective_user.id

    data = await get_weather_with_translation(city)

    if "error" in data:
        await update.message.reply_text(
            f"❌ {data['error']}",
            reply_markup=weather_actions_kb(),
        )
        logger.warning("Ошибка получения погоды: %s", data["error"])
        return END

    logger.info("Запись города %s в базу данных для пользователя %s", city, user_id)
    await set_user_city(user_id, city)

    desc = data["description"]
    temp = data["temp"]

    await update.message.reply_text(
        f"🌤 {city}\n{desc}\n🌡 Температура: {round(temp)}°C",
        reply_markup=weather_actions_kb(),
    )

    return END
