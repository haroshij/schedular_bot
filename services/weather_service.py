import aiohttp

from constants.weather_constants import WEATHER_TRANSLATIONS


async def get_weather(city: str) -> dict:
    """
    Получаем погоду через wttr.in (без API ключа, работает на Railway).
    Возвращает словарь с ключами 'weather' и 'main' или 'error'.
    """
    url = f"http://wttr.in/{city}?format=j1"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return {"error": f"Ошибка получения погоды ({resp.status})"}
                data = await resp.json()
        except Exception as e:
            return {"error": f"Не удалось подключиться к API: {e}"}

    try:
        current = data["current_condition"][0]
        description = current["weatherDesc"][0]["value"]
        temp = float(current["temp_C"])
        return {
            "weather": [{"description": description}],
            "main": {"temp": temp}
        }
    except Exception as e:
        return {"error": f"Ошибка обработки данных: {e}"}


# ------------------------------------------------------------------
# ДОБАВЛЕННАЯ ФУНКЦИЯ (для callbacks.py)
# ------------------------------------------------------------------

async def get_weather_with_translation(city: str) -> dict:
    data = await get_weather(city)
    if "error" in data:
        return data

    desc_en = data["weather"][0]["description"]
    return {
        "city": city,
        "description": translate_weather(desc_en),
        "temp": data["main"]["temp"],
    }


def translate_weather(desc: str) -> str:
    """Переводит английское описание погоды на русский, если есть в словаре."""
    desc = desc.capitalize()
    return WEATHER_TRANSLATIONS.get(desc, desc)
