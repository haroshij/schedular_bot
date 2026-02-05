from datetime import datetime, timezone, timedelta
import locale

# Попытка установить русскую локаль
try:
    locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")
except locale.Error:
    locale.setlocale(locale.LC_TIME, "")

# Московский часовой пояс
MOSCOW_TZ = timezone(timedelta(hours=3))
RU_DAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
RU_MONTHS = ["Января", "Февраля", "Марта", "Апреля", "Мая", "Июня",
             "Июля", "Августа", "Сентября", "Октября", "Ноября", "Декабря"]

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
