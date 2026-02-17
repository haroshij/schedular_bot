import pytest
from utils.weather_utils import validate_city, translate_weather


@pytest.mark.parametrize(
    "city",
    [
        "Moscow",
        "New York",
        "Berlin",
        "Санкт-Петербург",
        "Нижний Новгород",
        "Los-Angeles",
        "Ростов-на-Дону",
        "Rio de Janeiro",
        "Казань",
    ],
)
def test_validate_city_valid(city):
    """
    Проверка корректной валидации названий городов.
    """

    assert validate_city(city) is True


@pytest.mark.parametrize(
    "city",
    [
        "",  # пустая строка
        "A",  # слишком короткая
        "1Berlin",  # цифра в начале
        "Paris!",  # спецсимвол
        "New_York",  # underscore
        "São Paulo",  # символы типа (ã, õ)
        "VeryVeryVeryVeryVeryVeryVeryVeryVeryVeryLongCityName",  # >50 символов
        "Москва123",  # цифры в конце
    ],
)
def test_validate_city_invalid(city):
    """
    Проверка функции validate_city на недопустимые названия городов.
    """

    assert validate_city(city) is False


def test_translate_weather_known_value():
    """
    Проверка корректного перевода известных английских описаний погоды.
    """

    assert translate_weather("clear") == "Ясно"
    assert translate_weather("Clear") == "Ясно"
    assert translate_weather("RAIN") == "Дождь"


def test_translate_weather_unknown_value_returns_original():
    """
    Проверка поведения функции translate_weather для неизвестных значений.
    """

    assert translate_weather("Volcanic ash") == "Volcanic ash"
    assert translate_weather("Alien storm") == "Alien storm"


def test_translate_weather_capitalization():
    """
    Проверка корректного капитализирования входной строки перед переводом.
    """

    assert translate_weather("light rain") == "Небольшой дождь"
    assert translate_weather("LIGHT RAIN") == "Небольшой дождь"
