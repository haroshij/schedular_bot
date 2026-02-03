from datetime import datetime

def parse_datetime(text: str):
    """Парсинг даты и времени из строки формата YYYY-MM-DD HH:MM"""
    try:
        return datetime.strptime(text, "%Y-%m-%d %H:%M")
    except ValueError:
        return None

def format_task(task: dict):
    """Форматирование задачи для вывода"""
    return f"📝 {task['title']}\n⏰ {task['scheduled_time']}"
