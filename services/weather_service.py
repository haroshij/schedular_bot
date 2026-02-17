import aiohttp
import asyncio
import json
from app.redis_client import get_redis_client
from urllib.parse import quote

from utils.weather_utils import validate_city
from app.logger import logger
from utils.weather_utils import translate_weather


async def _get_weather(city: str) -> dict:
    """
    Получает текущую погоду для указанного города через сервис wttr.in.
    Функция выполняет HTTP-запрос к публичному сервису wttr.in,
    который не требует API-ключа и подходит для использования
    в облачных средах (например, Railway).
    Также данные в течение 10 минут будут храниться в Redis

    Args:
        city (str): Название города, для которого необходимо получить погоду.

    Returns:
        dict: Словарь с данными о погоде или словарь с описанием ошибки.
    """


    cache_key = f"weather:{city.lower()}"
    cache_ttl = 600
    redis_client = get_redis_client()

    if redis_client:
        cached = await redis_client.get(cache_key)  # Проверяем Redis cache
        if cached:
            logger.info("Погода для %s получена из Redis cache", city)
            return json.loads(cached)

    url = f"https://wttr.in/{quote(city)}?format=j1"
    timeout = aiohttp.ClientTimeout(
        total=60,
        connect=20,
        sock_connect=20,
        sock_read=20,
    )

    headers = {"User-Agent": "Mozilla/5.0"}

    retries = 5
    delay = 0.25

    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        for attempt in range(1, retries + 1):
            logger.debug("Попытка %s соединения с %s", attempt, url)

            try:
                async with session.get(url) as resp:
                    if resp.status != 200:  # type: ignore
                        logger.warning(
                            "Ошибка получения погоды с %s. Статус: %s",
                            url,
                            resp.status,
                        )
                        return {"error": f"Ошибка получения погоды ({resp.status})"}

                    data = await resp.json()
                    break

            except (TimeoutError, aiohttp.ClientError) as e:
                logger.warning(
                    "Ошибка подключения к %s (попытка %s/%s): \n%s",
                    url,
                    attempt,
                    retries,
                    e,
                )

            except Exception as e:
                logger.exception("Неожиданная ошибка при запросе к %s\n%s", url, e)

            if attempt == retries:
                return {"error": "Не удалось подключиться"}

            await asyncio.sleep(delay)
            delay *= 2

    try:
        current = data["current_condition"][0]
        description = current["weatherDesc"][0]["value"]
        temp = float(current["temp_C"])

        logger.debug("Обработка данных с %s прошла успешно", url)
        result = {
            "weather": [{"description": description}],
            "main": {"temp": temp},
        }

        if redis_client:
            await redis_client.setex(  # сохраняем в Redis
                cache_key,
                cache_ttl,
                json.dumps(result),
            )

        return result

    except Exception as e:
        logger.exception("Ошибка обработки ответа wttr.in\n%s", e)
        return {"error": "Ошибка обработки данных погоды"}


async def get_weather_with_translation(city: str) -> dict:
    """
    Получает текущую погоду для города и возвращает данные с переводом описания.

    Args:
        city (str): Название города, введённое пользователем.

    Returns:
        dict: Словарь с переведённым описанием погоды и температурой
        либо словарь с ключом `error` в случае ошибки.
    """

    logger.info("Запуск получения информации по погоде в городе %s", city)

    if not validate_city(city):
        logger.warning("Название города %s не валидировано", city)
        return {"error": "Некорректное название города"}

    data = await _get_weather(city)
    if "error" in data:
        return data

    desc_en = data["weather"][0]["description"]
    logger.debug("Получение информации по погоде в городе %s прошло успешно", city)

    return {
        "city": city,
        "description": translate_weather(desc_en),
        "temp": data["main"]["temp"],
    }
