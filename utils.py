from datetime import datetime, timezone, timedelta
import locale

# Попытка установить русскую локаль
try:
    locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")
except locale.Error:
    locale.setlocale(locale.LC_TIME, "")

# Московский часовой пояс
MOSCOW_TZ = timezone(timedelta(hours=3))
RU_DAYS = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]
RU_MONTHS = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн",
             "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]
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
    "Light snow": "Лёгкий снег",
    "Light snow, snow": "Лёгкий снег, снег",
    "Moderate snow": "Умеренный снег",
    "Heavy snow": "Сильный снег",
    "Snow": "Снег",
    "Blizzard": "Метель",

    # Смешанные осадки
    "Sleet": "Мокрый снег",
    "Light sleet": "Лёгкий мокрый снег",
    "Rain and snow": "Дождь со снегом",

    # Гроза
    "Thunderstorm": "Гроза",
    "Thunderstorms": "Грозы",
    "Patchy thunderstorm possible": "Возможна гроза",

    # Другие
    "Freezing fog": "Ледяной туман",
    "Partly Sunny": "Переменная облачность с солнцем",
}

def translate_weather(desc: str) -> str:
    """Переводит английское описание погоды на русский, если есть в словаре."""
    desc = desc.capitalize()
    return WEATHER_TRANSLATIONS.get(desc, desc)

def parse_datetime(text: str):
    """Парсинг даты и времени из строки формата YYYY-MM-DD HH:MM"""
    try:
        return datetime.strptime(text, "%Y-%m-%d %H:%M")
    except ValueError:
        return None

def format_task_date(dt_or_str) -> str:
    """
    Преобразует datetime или ISO-строку в читаемый формат на русском:
    Например: datetime -> "Суббота, 01 Октября 2222 10:00"
    """
    if isinstance(dt_or_str, str):
        dt = datetime.fromisoformat(dt_or_str.replace("Z", "+00:00"))
    elif isinstance(dt_or_str, datetime):
        dt = dt_or_str
    else:
        raise TypeError(f"Expected str or datetime, got {type(dt_or_str)}")

    # Приводим к московскому времени
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt_local = dt.astimezone(MOSCOW_TZ)

    day_name = RU_DAYS[dt_local.weekday()]
    month_name = RU_MONTHS[dt_local.month - 1]

    return f"{day_name}, {dt_local.day:02d} {month_name} {
    dt_local.year} {dt_local.hour:02d}:{dt_local.minute:02d}"

def format_task(task: dict) -> str:
    """Форматирует задачу для показа пользователю"""
    date_str = format_task_date(task["scheduled_time"])
    return f"📝 {task['title']}\n⏰ {date_str}"
