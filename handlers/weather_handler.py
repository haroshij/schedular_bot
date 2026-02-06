from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

from handlers.weather import get_weather
from database import set_user_city  # подключаем функцию для сохранения города


async def weather_handler(update: Update, _: CallbackContext):
    city = update.message.text.strip()
    user_id = update.effective_user.id

    data = await get_weather(city)

    if "error" in data:
        await update.message.reply_text(f"❌ {data['error']}")
        return

    # Сохраняем город в базе после успешного получения погоды
    await set_user_city(user_id, city)

    desc = data["weather"][0]["description"]
    temp = data["main"]["temp"]

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Другой город", callback_data="weather_change")],
        [InlineKeyboardButton("↩️ В меню", callback_data="menu")]
    ])

    await update.message.reply_text(
        f"🌤 {city}:\n"
        f"{desc}\n"
        f"🌡 Температура: {temp}°C",
        reply_markup=kb
    )
