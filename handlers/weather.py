import aiohttp
from telegram import Update
from telegram.ext import CallbackContext
from database import set_user_city
from keyboard import MAIN_MENU

API_KEY = "2de2b5931c1e24a55a93626e533d8657"

async def get_weather(city: str) -> dict:
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
        "lang": "ru"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                return {"weather": [{"description": "Ошибка получения погоды"}], "main": {"temp": "?"}}
            return await resp.json()

async def weather_handler(update: Update, _: CallbackContext):
    query = update.callback_query
    if query:
        city = query.data if query.data else "Moscow"  # fallback
        await set_user_city(query.from_user.id, city)
        data = await get_weather(city)
        description = data.get("weather", [{"description": "Нет данных"}])[0]["description"]
        temp = data.get("main", {}).get("temp", "?")
        await query.edit_message_text(f"🌤 {city}\n{description}\n🌡 {temp}°C", reply_markup=MAIN_MENU)
    elif update.message:
        city = update.message.text
        await set_user_city(update.message.from_user.id, city)
        data = await get_weather(city)
        description = data.get("weather", [{"description": "Нет данных"}])[0]["description"]
        temp = data.get("main", {}).get("temp", "?")
        await update.message.reply_text(f"🌤 {city}\n{description}\n🌡 {temp}°C", reply_markup=MAIN_MENU)
