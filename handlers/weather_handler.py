from telegram import Update
from telegram.ext import CallbackContext

from keyboard import weather_actions_kb
from services.weather_service import get_weather
from services.weather_service import translate_weather
from database import set_user_city  # подключаем функцию для сохранения города


async def weather_handler(update: Update, _: CallbackContext):
    city = update.message.text.strip()
    user_id = update.effective_user.id

    data = await get_weather(city)

    if "error" in data:
        await update.message.reply_text(f"❌ {data['error']}",
                                        reply_markup=weather_actions_kb())
        return

    # Сохраняем город в базе после успешного получения погоды
    await set_user_city(user_id, city)

    desc = data["weather"][0]["description"]
    desc_ru = translate_weather(desc)
    temp = data["main"]["temp"]

    await update.message.reply_text(
        f"🌤 {city}:\n"
        f"{desc_ru}\n"
        f"🌡 Температура: {round(temp)}°C",
        reply_markup=weather_actions_kb()
    )
