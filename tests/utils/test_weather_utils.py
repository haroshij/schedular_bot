import pytest

from utils.weather_utils import validate_city, translate_weather


# validate_city
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
    assert validate_city(city) is True


@pytest.mark.parametrize(
    "city",
    [
        "",
        "A",                    # слишком короткое
        "1Berlin",              # цифры
        "Paris!",               # спецсимволы
        "New_York",             # underscore запрещён
        "São Paulo",            # diacritics (ã, õ) не проходят regex
        "VeryVeryVeryVeryVeryVeryVeryVeryVeryVeryLongCityName",  # > 50 символов
        "Москва123",
    ],
)
def test_validate_city_invalid(city):
    assert validate_city(city) is False


# translate_weather
def test_translate_weather_known_value():
    assert translate_weather("clear") == "Ясно"
    assert translate_weather("Clear") == "Ясно"
    assert translate_weather("RAIN") == "Дождь"


def test_translate_weather_unknown_value_returns_original():
    assert translate_weather("Volcanic ash") == "Volcanic ash"
    assert translate_weather("Alien storm") == "Alien storm"


def test_translate_weather_capitalization():
    """
    Проверяем, что функция корректно капитализирует входную строку
    перед поиском в словаре.
    """
    assert translate_weather("light rain") == "Небольшой дождь"
    assert translate_weather("LIGHT RAIN") == "Небольшой дождь"
