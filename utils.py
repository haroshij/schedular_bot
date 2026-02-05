from datetime import datetime
import locale

# Попытка установить русскую локаль
try:
    locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")
except locale.Error:
    # Если локаль отсутствует, используем системную по умолчанию
    locale.setlocale(locale.LC_TIME, "")


def parse_datetime(text: str):
    """
    Парсинг даты и времени из строки формата YYYY-MM-DD HH:MM
    Возвращает datetime или None при ошибке
    """
    try:
        return datetime.strptime(text, "%Y-%m-%d %H:%M")
    except ValueError:
        return None


def format_task_date(dt_or_str) -> str:
    """
    Преобразует datetime или ISO-строку из базы в читаемый формат для пользователя.
    Например:
        datetime(2222, 10, 1, 10, 0) -> "Суббота, 01 Октября 2222 10:00"
        "2222-10-01T10:00:00+00:00" -> "Суббота, 01 Октября 2222 10:00"
    """
    if isinstance(dt_or_str, str):
        # Поддержка строк из базы с таймзоной
        dt = datetime.fromisoformat(dt_or_str.replace("Z", "+00:00"))
    elif isinstance(dt_or_str, datetime):
        dt = dt_or_str
    else:
        raise TypeError(f"Expected str or datetime, got {type(dt_or_str)}")

    return dt.strftime("%A, %d %b %Y %H:%M")


def format_task(task: dict) -> str:
    """
    Форматирует задачу для показа пользователю.
    Показывает название и дату/время в удобочитаемом виде.
    """
    date_str = format_task_date(task["scheduled_time"])
    return f"📝 {task['title']}\n⏰ {date_str}"
