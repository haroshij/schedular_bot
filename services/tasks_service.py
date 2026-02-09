from uuid import uuid4
from datetime import datetime, timezone

from database import (
    add_task,
    update_task_time,
    get_task_by_id,
    get_all_tasks,
    get_nearest_task,
    mark_task_done,
)
from app.logger import logger


async def create_task(user_id: int, title: str, scheduled_time: datetime) -> dict:
    """
    Создаёт задачу в БД и возвращает объект задачи.
    """
    task_id = str(uuid4())
    logger.debug('Запрос к БД для создания задачи пользователем %s', user_id)
    await add_task(task_id, user_id, title, scheduled_time)
    task = await get_task_by_id(task_id)
    return task


async def change_task_time(task_id: str, new_time: datetime) -> dict:
    """
    Обновляет время задачи и возвращает обновлённый объект задачи.
    """
    logger.debug('Запрос к БД для переноса задачи %s', task_id)
    await update_task_time(task_id, new_time)
    task = await get_task_by_id(task_id)
    return task


# ------------------------------------------------------------------
# ДОБАВЛЕННЫЕ ФУНКЦИИ (для callbacks.py)
# ------------------------------------------------------------------

async def get_task(task_id: str) -> dict | None:
    logger.debug('Запрос к БД для получения задачи %s', task_id)
    return await get_task_by_id(task_id)


async def get_tasks(user_id: int) -> list[dict]:
    logger.debug('Запрос к БД для получения всех задач пользователя %s', user_id)
    return await get_all_tasks(user_id)


async def get_nearest_user_task(user_id: int) -> dict | None:
    logger.debug('Запрос к БД для получения ближайшей задачи пользователя %s', user_id)
    return await get_nearest_task(user_id)


async def complete_task(task_id: str) -> None:
    logger.debug('Запрос к БД для перевода задачи %s в состояние "done"', task_id)
    await mark_task_done(task_id)
