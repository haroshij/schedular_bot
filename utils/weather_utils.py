import re
from constants.weather_constants import WEATHER_TRANSLATIONS

CITY_RE = re.compile(r"^[A-Za-zА-Яа-яЁё \-]{2,50}$")


def validate_city(city: str) -> bool:
    """
    Проверяет корректность названия города, введённого пользователем.
    """

    return bool(CITY_RE.match(city))


def translate_weather(desc: str) -> str:
    """
    Переводит английское описание погоды на русский язык, если перевод доступен.

    Args:
        desc (str): Описание погоды на английском языке.

    Returns:
        str: Переведённое описание погоды на русском языке,
             либо оригинальное описание, если перевод не найден.
    """

    desc = desc.capitalize()

    return WEATHER_TRANSLATIONS.get(desc, desc)
