import aiohttp
from database import set_user_city

API_KEY = "2de2b5931c1e24a55a93626e533d8657"

async def get_weather(city: str) -> dict:
    """
    Получение погоды через прокси PythonAnywhere.
    Работает на Free-плане.
    """
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
        "lang": "ru"
    }

    proxy = "http://proxy.pythonanywhere.com:3128"  # специальный прокси PA Free

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, proxy=proxy) as resp:
                if resp.status != 200:
                    return {"error": f"Ошибка получения погоды ({resp.status})"}
                data = await resp.json()
    except Exception as e:
        return {"error": f"Не удалось подключиться к API: {e}"}

    await set_user_city(user_id=None, city=city)
    return data
