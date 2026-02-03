from datetime import datetime
from typing import Dict


def parse_datetime(text: str) -> datetime | None:
    """Парсит дату из строки в формате YYYY-MM-DD HH:MM"""
    try:
        return datetime.strptime(text.strip(), "%Y-%m-%d %H:%M")
    except ValueError:
        return None


def format_task(task: Dict) -> str:
    """Форматирует задачу для отображения пользователю"""
    title = task.get("title", "Без названия")
    scheduled_time = task.get("scheduled_time", "?")

    # Если scheduled_time хранится как ISO, можно преобразовать
    if isinstance(scheduled_time, str):
        try:
            dt = datetime.fromisoformat(scheduled_time)
            scheduled_time = dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            pass

    status = task.get("status", "pending")
    status_icon = "✅" if status == "done" else "⏳"

    return f"{status_icon} 📝 {title}\n⏰ {scheduled_time}"
