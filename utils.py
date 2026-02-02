from datetime import timedelta

def parse_time_interval(text):
    """
    Преобразует текст вроде "10m", "1h", "2d" в timedelta
    Поддерживаем:
        m - минуты
        h - часы
        d - дни
        w - недели
    """
    unit = text[-1]
    value = int(text[:-1])

    if unit == "m":
        return timedelta(minutes=value)
    elif unit == "h":
        return timedelta(hours=value)
    elif unit == "d":
        return timedelta(days=value)
    elif unit == "w":
        return timedelta(weeks=value)
    else:
        raise ValueError("Неподдерживаемый формат времени. Используй m, h, d, w.")

def format_task(task):
    """Красивый вывод задачи"""
    repeat = f", повтор каждые {task.repeat_interval}" if task.repeat_interval else ""
    return f"{task.title} | Время: {task.scheduled_time}{repeat} | Приоритет: {task.priority}"
