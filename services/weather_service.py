import aiohttp
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

    На выходе функция либо возвращает нормализованный словарь
    с погодными данными (температура и описание),
    либо словарь с ключом `error` в случае любой ошибки:
    - сетевой ошибки;
    - некорректного HTTP-статуса;
    - ошибки обработки JSON-ответа.

    Args:
        city (str): Название города, для которого необходимо получить погоду.

    Returns:
        dict: Словарь с данными о погоде или словарь с описанием ошибки.
    """
    # Формируем URL запроса к сервису wttr.in в формате JSON
    url = f"https://wttr.in/{quote(city)}?format=j1"

    timeout = aiohttp.ClientTimeout(
        total=20,
        connect=10,
        sock_connect=10,
        sock_read=20,
    )
    headers = {"User-Agent": "Mozilla/5.0"}
    # Создаём HTTP-сессию для выполнения асинхронного запроса
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        logger.debug("Попытка соединения с %s...", url)
        try:
            # Выполняем GET-запрос
            async with session.get(url) as resp:
                if resp.status != 200:
                    logger.warning(
                        "Ошибка получения погоды с %s. Статус: %s", url, resp.status
                    )
                    return {"error": f"Ошибка получения погоды ({resp.status})"}

                data = await resp.json()
        except Exception as e:
            logger.exception("Ошибка подключения к %s\n%s", url, e)
            return {"error": "Не удалось подключиться"}

    try:
        # Извлекаем текущие погодные условия
        current = data["current_condition"][0]
        description = current["weatherDesc"][0]["value"]
        temp = float(current["temp_C"])

        logger.debug("Обработка данных, полученных с %s, прошла успешно", url)

        # Возвращаем данные в унифицированном формате
        return {"weather": [{"description": description}], "main": {"temp": temp}}
    except Exception as e:
        logger.warning("Ошибка обработки данных\n%s", e)
        return {"error": f"Ошибка обработки данных: {e}"}


async def get_weather_with_translation(city: str) -> dict:
    """
    Получает текущую погоду для города и возвращает данные с переводом описания.

    Функция является публичным интерфейсом сервиса погоды
    и используется в обработчиках Telegram-бота.

    Последовательность действий:
    1. Проверяет валидность названия города.
    2. Запрашивает данные о погоде через `_get_weather`.
    3. Обрабатывает возможные ошибки.
    4. Переводит описание погоды на русский язык.
    5. Возвращает готовый к отображению результат.

    Args:
        city (str): Название города, введённое пользователем.

    Returns:
        dict: Словарь с переведённым описанием погоды и температурой
        либо словарь с ключом `error` в случае ошибки.
    """
    # Логируем начало получения информации о погоде
    logger.info("Запуск получения информации по погоде в городе %s", city)

    # Проверяем корректность названия города
    if not validate_city(city):
        logger.warning("Название города %s не валидировано", city)
        return {"error": "Некорректное название города"}

    # Получаем сырые данные о погоде
    data = await _get_weather(city)

    # Если при получении погоды произошла ошибка — возвращаем её сразу
    if "error" in data:
        return data

    # Извлекаем английское описание погоды
    desc_en = data["weather"][0]["description"]

    # Логируем успешное получение погодных данных
    logger.debug("Получение информации по погоде в городе %s прошло успешно", city)

    # Формируем итоговый словарь для использования в боте
    return {
        "city": city,
        "description": translate_weather(desc_en),
        "temp": data["main"]["temp"],
    }
