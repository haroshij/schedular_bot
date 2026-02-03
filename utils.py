from datetime import datetime
import locale

try:
    locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")
except locale.Error:
    # Если на системе нет русской локали, используем английскую
    locale.setlocale(locale.LC_TIME, "")


def parse_datetime(text: str):
    """Парсинг даты и времени из строки формата YYYY-MM-DD HH:MM"""
    try:
        return datetime.strptime(text, "%Y-%m-%d %H:%M")
    except ValueError:
        return None


def format_task_date(iso_string: str) -> str:
    """
    Преобразует ISO-строку из базы в читаемый формат для пользователя.
    Например: "2222-10-01T10:00:00" -> "Суббота, 01 Октября 2222 10:00"
    """
    dt = datetime.fromisoformat(iso_string)
    return dt.strftime("%A, %d %b %Y %H:%M")


def format_task(task: dict) -> str:
    """
    Форматирует задачу для показа пользователю.
    Показывает название и дату/время в удобочитаемом виде.
    """
    date_str = format_task_date(task["scheduled_time"])
    return f"📝 {task['title']}\n⏰ {date_str}"
