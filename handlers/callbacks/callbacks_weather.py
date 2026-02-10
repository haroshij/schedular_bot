from telegram import Update
from telegram.ext import CallbackContext

from handlers.common.common import cancel_menu_kb
from states import WEATHER_CITY
from database import get_user_city
from services.weather_service import get_weather_with_translation
from keyboard import weather_actions_kb
from app.decorators import log_handler
from app.logger import logger


@log_handler
async def handle_weather_callbacks(update: Update, _: CallbackContext, data: str):
    query = update.callback_query
    user_id = update.effective_user.id
    logger.info("Пользователь %s запросил погоду", user_id)

    if data in ("weather", "weather_change"):
        city = await get_user_city(user_id)

        if city and data == "weather":
            weather = await get_weather_with_translation(city)

            if "error" in weather:
                text = f"❌ {weather['error']}"
                logger.warning('Ошибка получения погоды: %s', weather['error'])
            else:
                text = (
                    f"🌤 {weather['city'].title()}\n"
                    f"{weather['description'].capitalize()}\n"
                    f"🌡 {round(weather['temp'])}°C"
                )

            await query.edit_message_text(text, reply_markup=weather_actions_kb())
            logger.info('Отправлена погода пользователю %s | city=%s', user_id, city)
            return None

        await query.edit_message_text(
            "Введите город:",
            reply_markup=cancel_menu_kb()
        )
        return WEATHER_CITY

    return None
