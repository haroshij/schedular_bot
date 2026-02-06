from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

from handlers.weather import get_weather


async def weather_handler(update: Update, _: CallbackContext):
    city = update.message.text.strip()
    data = await get_weather(city)

    if "error" in data:
        await update.message.reply_text(f"❌ {data['error']}")
        return

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
        reply_markup = kb
    )
