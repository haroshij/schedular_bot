"""
Модуль с константами для перевода погодных условий.

Содержит словарь WEATHER_TRANSLATIONS, который переводит
англоязычные описания погоды в русский язык.
"""

WEATHER_TRANSLATIONS = {
    # Ясные/солнечные условия
    "Clear": "Ясно",
    "Sunny": "Солнечно",
    "Mostly Sunny": "В основном солнечно",

    # Облачно
    "Partly cloudy": "Переменная облачность",
    "Mostly Cloudy": "Преимущественно облачно",
    "Cloudy": "Облачно",
    "Overcast": "Пасмурно",

    # Туман/дым
    "Fog": "Туман",
    "Mist": "Лёгкий туман",
    "Haze": "Мгла",

    # Дождь
    "Light rain": "Небольшой дождь",
    "Patchy rain possible": "Возможен кратковременный дождь",
    "Patchy rain nearby": "Небольшой дождь поблизости",
    "Moderate rain": "Умеренный дождь",
    "Heavy rain": "Сильный дождь",
    "Light drizzle": "Морось",
    "Rain": "Дождь",
    "Rain showers": "Ливневые дожди",
    "Showers": "Ливни",

    # Снег / лед
    "Light freezing rain": "Лёгкий ледяной дождь",
    "Light snow": "Лёгкий снег",
    "Light snow, snow": "Лёгкий снег, снег",
    "Light snow shower": "Лёгкий снежный дождь",
    "Moderate snow": "Умеренный снег",
    "Heavy snow": "Сильный снег",
    "Snow": "Снег",
    "Blizzard": "Метель",

    # Смешанные осадки
    "Sleet": "Мокрый снег",
    "Light sleet": "Лёгкий мокрый снег",
    "Rain and snow": "Дождь со снегом",
    "Light drizzle, mist": "Лёгкая морось, туман",

    # Гроза
    "Thunderstorm": "Гроза",
    "Thunderstorms": "Грозы",
    "Patchy thunderstorm possible": "Возможна гроза",

    # Другие погодные условия
    "Freezing fog": "Ледяной туман",
    "Partly Sunny": "Переменная облачность с солнцем",
}
