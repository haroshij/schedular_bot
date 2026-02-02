import json
from pathlib import Path
from task import Task
from datetime import datetime, timedelta

STORAGE_FILE = Path("tasks.json")

def save_tasks(tasks):
    """Сохраняем список задач в JSON"""
    data = []
    for task in tasks:
        data.append({
            "id": task.id,
            "title": task.title,
            "user_id": task.user_id,
            "scheduled_time": task.scheduled_time.isoformat(),
            "priority": task.priority,
            "repeat_interval": task.repeat_interval.total_seconds() if task.repeat_interval else None,
            "completed": task.completed
        })
    with STORAGE_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_tasks():
    """Загружаем задачи из JSON и возвращаем список Task"""
    if not STORAGE_FILE.exists():
        return []

    with STORAGE_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    tasks = []
    for item in data:
        repeat_interval = timedelta(seconds=item["repeat_interval"]) if item["repeat_interval"] else None
        scheduled_time = datetime.fromisoformat(item["scheduled_time"])
        task = Task(
            title=item["title"],
            user_id=item["user_id"],
            scheduled_time=scheduled_time,
            priority=item["priority"],
            repeat_interval=repeat_interval
        )
        task.id = item["id"]
        task.completed = item["completed"]
        tasks.append(task)
    return tasks
