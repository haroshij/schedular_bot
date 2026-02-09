import aiohttp

from constants.weather_constants import WEATHER_TRANSLATIONS
from utils.weather_utils import validate_city
from app.logger import logger


async def _get_weather(city: str) -> dict:
    """
    Получаем погоду через wttr.in (без API ключа, работает на Railway).
    Возвращает словарь с ключами 'weather' и 'main' или 'error'.
    """
    url = f"https://wttr.in/{city}?format=j1"

    async with aiohttp.ClientSession() as session:
        logger.info('Попытка соединения с %s...', url)
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return {"error": f"Ошибка получения погоды ({resp.status})"}
                logger.warning('Ошибка получения погоды с %s. Статус: %s', url, resp.status)
                data = await resp.json()
        except Exception as e:
            logger.warning('Ошибка подключения к %s\n%s', url, e)
            return {"error": f"Не удалось подключиться: {e}"}

    try:
        current = data["current_condition"][0]
        description = current["weatherDesc"][0]["value"]
        temp = float(current["temp_C"])
        logger.info('Обработка данных, полученных с %s, прошла успешно', url)
        return {
            "weather": [{"description": description}],
            "main": {"temp": temp}
        }
    except Exception as e:
        logger.warning('Ошибка обработки данных\n%s', e)
        return {"error": f"Ошибка обработки данных: {e}"}


# ------------------------------------------------------------------
# ДОБАВЛЕННАЯ ФУНКЦИЯ (для callbacks.py)
# ------------------------------------------------------------------

async def get_weather_with_translation(city: str) -> dict:
    logger.info('Запуск получения информации по погоде в городе %s', city)
    if not validate_city(city):
        logger.warning('Название города %s не валидировано', city)
        return {"error": "Некорректное название города"}

    data = await _get_weather(city)
    if "error" in data:
        return data

    desc_en = data["weather"][0]["description"]
    logger.info('Получение информации по погоде в городе %s прошло успешно', city)
    return {
        "city": city,
        "description": translate_weather(desc_en),
        "temp": data["main"]["temp"],
    }


def translate_weather(desc: str) -> str:
    """Переводит английское описание погоды на русский, если есть в словаре."""
    desc = desc.capitalize()
    return WEATHER_TRANSLATIONS.get(desc, desc)
