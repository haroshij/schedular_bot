from uuid import uuid4
from datetime import datetime

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
    Создаёт новую задачу пользователя и сохраняет её в базе данных.
    Используется UUID, чтобы гарантировать уникальность задачи
    независимо от пользователя и времени создания.

    Args:
        user_id (int): Идентификатор пользователя, которому принадлежит задача.
        title (str): Текстовое описание (заголовок) задачи.
        scheduled_time (datetime): Дата и время выполнения задачи.

    Returns:
        dict: Объект задачи, полученный из базы данных после создания.
    """

    task_id = str(uuid4())  # Генерируем уникальный идентификатор задачи
    logger.debug("Запрос к БД для создания задачи пользователем %s", user_id)
    await add_task(task_id, user_id, title, scheduled_time)
    task = await get_task_by_id(task_id)

    return task  # Возвращаем созданную задачу из БД для создания напоминания


async def change_task_time(task_id: str, new_time: datetime) -> dict:
    """
    Обновляет дату и время выполнения существующей задачи.

    Функция изменяет запланированное время задачи в базе данных,
    а затем повторно извлекает задачу, чтобы вернуть её
    актуальное состояние после изменения.

    Args:
        task_id (str): Уникальный идентификатор задачи.
        new_time (datetime): Новая дата и время выполнения задачи.

    Returns:
        dict: Обновлённый объект задачи из базы данных.
    """

    logger.debug("Запрос к БД для переноса задачи %s", task_id)
    await update_task_time(task_id, new_time)
    task = await get_task_by_id(task_id)

    return task  # Возвращаем созданную задачу из БД для создания напоминания


async def get_task(task_id: str) -> dict | None:
    """
    Получает задачу по её идентификатору.

    Args:
        task_id (str): Уникальный идентификатор задачи.

    Returns:
        dict | None: Объект задачи, если она найдена,
        либо None, если задача с таким идентификатором отсутствует.
    """

    logger.debug("Запрос к БД для получения задачи %s", task_id)

    return await get_task_by_id(task_id)


async def get_tasks(user_id: int) -> list[dict]:
    """
    Получает список всех задач пользователя.

    Args:
        user_id (int): Идентификатор пользователя.

    Returns:
        list[dict]: Список объектов задач пользователя.
    """

    logger.debug("Запрос к БД для получения всех задач пользователя %s", user_id)

    return await get_all_tasks(user_id)


async def get_nearest_user_task(user_id: int) -> dict | None:
    """
    Получает ближайшую по времени выполнения задачу пользователя.

    Args:
        user_id (int): Идентификатор пользователя.

    Returns:
        dict | None: Объект ближайшей задачи,
        либо None, если у пользователя нет задач.
    """

    logger.debug("Запрос к БД для получения ближайшей задачи пользователя %s", user_id)

    return await get_nearest_task(user_id)


async def complete_task(task_id: str) -> None:
    """
    Помечает задачу как выполненную.

    Args:
        task_id (str): Уникальный идентификатор задачи.

    Returns:
        None
    """

    logger.debug('Запрос к БД для перевода задачи %s в состояние "done"', task_id)

    await mark_task_done(task_id)
