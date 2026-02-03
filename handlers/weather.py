import aiohttp
from database import set_user_city

API_KEY = "2de2b5931c1e24a55a93626e533d8657"

async def get_weather(city: str) -> dict:
    """
    Асинхронный запрос к OpenWeatherMap API.
    Возвращает данные погоды или ошибку.
    """
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
        "lang": "ru"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return {"error": f"Ошибка получения погоды ({resp.status})"}
                data = await resp.json()
        except Exception as e:
            return {"error": str(e)}

    # Если город найден, сохраняем в БД
    await set_user_city(user_id=None, city=city)  # Можно убрать user_id, если не нужен
    return data
