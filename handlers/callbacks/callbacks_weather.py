from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

from handlers.common import cancel_menu_kb
from states import WEATHER_CITY
from database import get_user_city
from services.weather_service import get_weather_with_translation


async def handle_weather_callbacks(update: Update, _: CallbackContext, data: str):
    query = update.callback_query
    user_id = update.effective_user.id

    if data in ("weather", "weather_change"):
        city = await get_user_city(user_id)

        if city and data == "weather":
            weather = await get_weather_with_translation(city)

            if "error" in weather:
                text = f"❌ {weather['error']}"
            else:
                text = (
                    f"🌤 {weather['city'].title()}\n"
                    f"{weather['description'].capitalize()}\n"
                    f"🌡 {round(weather['temp'])}°C"
                )

            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Другой город", callback_data="weather_change")],
                [InlineKeyboardButton("↩️ В меню", callback_data="menu")]
            ])

            await query.edit_message_text(text, reply_markup=kb)
            return True

        await query.edit_message_text(
            "Введите город:",
            reply_markup=cancel_menu_kb()
        )
        return WEATHER_CITY

    return None
