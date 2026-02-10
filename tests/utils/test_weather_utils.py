import pytest

from utils.weather_utils import validate_city, translate_weather


# Тесты функции validate_city
@pytest.mark.parametrize(
    "city",
    [
        "Moscow",  # латиница
        "New York",  # латиница с пробелом
        "Berlin",  # латиница
        "Санкт-Петербург",  # кириллица с дефисом
        "Нижний Новгород",  # кириллица с пробелом
        "Los-Angeles",  # латиница с дефисом
        "Ростов-на-Дону",  # кириллица с дефисом
        "Rio de Janeiro",  # латиница с пробелами
        "Казань",  # кириллица
    ],
)
def test_validate_city_valid(city):
    """
    Проверка корректной валидации названий городов.

    Функция validate_city должна вернуть True для городов:
    - длина строки от 2 до 50 символов
    - содержит только буквы (латиница или кириллица), пробелы и дефисы
    - корректно обрабатывает кириллицу и латиницу
    """
    # Проверяем, что валидные города проходят проверку
    assert validate_city(city) is True


@pytest.mark.parametrize(
    "city",
    [
        "",  # пустая строка
        "A",  # слишком короткая
        "1Berlin",  # цифра в начале
        "Paris!",  # спецсимвол
        "New_York",  # underscore запрещён
        "São Paulo",  # диакритические символы (ã, õ) не проходят regex
        "VeryVeryVeryVeryVeryVeryVeryVeryVeryVeryLongCityName",  # >50 символов
        "Москва123",  # цифры в конце
    ],
)
def test_validate_city_invalid(city):
    """
    Проверка функции validate_city на недопустимые названия городов.

    Функция validate_city должна вернуть False для:
    - пустой строки
    - слишком коротких названий
    - названий с цифрами, спецсимволами или недопустимыми символами
    - названий длиной более 50 символов
    """
    assert validate_city(city) is False


# Тесты функции translate_weather
def test_translate_weather_known_value():
    """
    Проверка корректного перевода известных английских описаний погоды.

    Функция translate_weather должна:
    - искать описание в словаре WEATHER_TRANSLATIONS
    - возвращать перевод на русский язык
    - быть нечувствительной к регистру (capitalize перед поиском)
    """
    assert translate_weather("clear") == "Ясно"
    assert translate_weather("Clear") == "Ясно"
    assert translate_weather("RAIN") == "Дождь"


def test_translate_weather_unknown_value_returns_original():
    """
    Проверка поведения функции translate_weather для неизвестных значений.

    Функция должна:
    - возвращать исходную строку, если описания нет в словаре
    - корректно обрабатывать любые неизвестные английские фразы
    """
    assert translate_weather("Volcanic ash") == "Volcanic ash"
    assert translate_weather("Alien storm") == "Alien storm"


def test_translate_weather_capitalization():
    """
    Проверка корректного капитализирования входной строки перед переводом.

    Функция должна:
    - игнорировать регистр входной строки
    - корректно искать описание в словаре после капитализации
    - возвращать правильный перевод на русский
    """
    # Проверяем перевод с разными регистрами
    assert translate_weather("light rain") == "Небольшой дождь"
    assert translate_weather("LIGHT RAIN") == "Небольшой дождь"
