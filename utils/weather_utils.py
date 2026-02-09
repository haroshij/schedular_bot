import re

from constants.weather_constants import WEATHER_TRANSLATIONS

CITY_RE = re.compile(r"^[A-Za-zА-Яа-яЁё \-]{2,50}$")


def validate_city(city: str) -> bool:
    return bool(CITY_RE.match(city))


def translate_weather(desc: str) -> str:
    """Переводит английское описание погоды на русский, если есть в словаре."""
    desc = desc.capitalize()
    return WEATHER_TRANSLATIONS.get(desc, desc)
