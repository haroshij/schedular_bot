from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

from keyboard import weather_actions_kb
from services.weather_service import get_weather_with_translation
from database import set_user_city  # подключаем функцию для сохранения города
from app.decorators import log_handler
from app.logger import logger


@log_handler
async def weather_handler(update: Update, _: CallbackContext):
    city = update.message.text.strip()
    user_id = update.effective_user.id

    data = await get_weather_with_translation(city)

    if "error" in data:
        await update.message.reply_text(
            f"❌ {data['error']}",
            reply_markup=weather_actions_kb())
        return ConversationHandler.END

    # Сохраняем город в базе после успешного получения погоды
    logger.info("Запрос к БД по сохранению города %s для пользователя %s", city, user_id)
    await set_user_city(user_id, city)

    desc = data["description"]
    temp = data["temp"]

    await update.message.reply_text(
        f"🌤 {city}:\n"
        f"{desc}\n"
        f"🌡 Температура: {round(temp)}°C",
        reply_markup=weather_actions_kb()
    )

    return ConversationHandler.END