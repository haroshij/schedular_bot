from uuid import uuid4
from datetime import datetime, timezone, timedelta

from database import add_task, update_task_time, get_task_by_id
from utils import parse_datetime

USER_TZ = timezone(timedelta(hours=3))


async def create_task(user_id: int, title: str, scheduled_time: datetime) -> dict:
    """
    Создаёт задачу в БД и возвращает объект задачи.
    """
    task_id = str(uuid4())
    await add_task(task_id, user_id, title, scheduled_time)
    task = await get_task_by_id(task_id)
    return task


async def change_task_time(task_id: str, new_time: datetime) -> dict:
    """
    Обновляет время задачи и возвращает обновлённый объект задачи.
    """
    await update_task_time(task_id, new_time)
    task = await get_task_by_id(task_id)
    return task


def parse_and_validate_datetime(text: str) -> datetime | None:
    """
    Парсит дату из текста и проверяет, что она в будущем.
    Возвращает datetime в UTC или None при ошибке.
    """
    dt = parse_datetime(text)
    if not dt:
        return None

    dt_utc = dt.replace(tzinfo=USER_TZ).astimezone(timezone.utc)
    if dt_utc < datetime.now(timezone.utc):
        return None

    return dt_utc
