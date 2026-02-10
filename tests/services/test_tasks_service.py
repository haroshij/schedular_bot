import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
import sys

"""
Тестовый модуль для services.tasks_service.

Содержит unit-тесты для сервисного слоя работы с задачами.
Задача тестов — проверить, что:
- сервис корректно вызывает функции слоя database;
- возвращаемые значения проксируются без искажений;
- все функции работают асинхронно и ожидают нужные вызовы.

Реальная база данных не используется — все обращения к ней замоканы.
"""

# Мокаем модуль database ДО импорта tasks_service
# Это критически важно:
# tasks_service импортирует функции из database на уровне модуля.
# Если не подменить database заранее, Python попытается импортировать
# реальный модуль database, что приведёт к ошибке.
mock_database = AsyncMock()
sys.modules['database'] = mock_database

from services.tasks_service import (
    create_task,
    change_task_time,
    get_task,
    get_tasks,
    get_nearest_user_task,
    complete_task,
)


# create_task
@pytest.mark.asyncio
async def test_create_task():
    """
    Проверяет создание задачи.

    Сценарий:
    - генерируется task_id;
    - вызывается add_task с нужными аргументами;
    - затем задача извлекается через get_task_by_id;
    - сервис возвращает полученный объект задачи.
    """
    fake_task = {
        "id": "task-id",
        "user_id": 1,
        "title": "Test task",
        "scheduled_time": datetime(2026, 2, 10, 12, 0),
    }

    # Мокаем функции database внутри tasks_service
    with patch("services.tasks_service.add_task", new_callable=AsyncMock) as add_task_mock, \
            patch("services.tasks_service.get_task_by_id", new_callable=AsyncMock) as get_task_mock:
        get_task_mock.return_value = fake_task

        result = await create_task(
            user_id=1,
            title="Test task",
            scheduled_time=fake_task["scheduled_time"],
        )

        # Проверяем, что БД была вызвана
        add_task_mock.assert_awaited_once()
        get_task_mock.assert_awaited_once()

        # Проверяем возвращаемое значение
        assert result == fake_task


# change_task_time
@pytest.mark.asyncio
async def test_change_task_time():
    """
    Проверяет изменение времени выполнения задачи.

    Сценарий:
    - вызывается update_task_time;
    - затем обновлённая задача запрашивается через get_task_by_id;
    - сервис возвращает обновлённую задачу.
    """
    new_time = datetime(2026, 3, 1, 10, 0)
    fake_task = {
        "id": "task-id",
        "scheduled_time": new_time,
    }

    with patch("services.tasks_service.update_task_time", new_callable=AsyncMock) as update_mock, \
            patch("services.tasks_service.get_task_by_id", new_callable=AsyncMock) as get_task_mock:
        get_task_mock.return_value = fake_task

        result = await change_task_time("task-id", new_time)

        # Проверяем корректность вызовов
        update_mock.assert_awaited_once_with("task-id", new_time)
        get_task_mock.assert_awaited_once_with("task-id")

        assert result == fake_task


# get_task
@pytest.mark.asyncio
async def test_get_task():
    """
    Проверяет получение одной задачи по id.

    Сервис должен просто проксировать вызов get_task_by_id
    и вернуть результат без изменений.
    """
    fake_task = {"id": "task-id"}

    with patch("services.tasks_service.get_task_by_id", new_callable=AsyncMock) as mock:
        mock.return_value = fake_task

        result = await get_task("task-id")

        mock.assert_awaited_once_with("task-id")
        assert result == fake_task


# get_tasks
@pytest.mark.asyncio
async def test_get_tasks():
    """
    Проверяет получение списка задач пользователя.

    Сервис вызывает get_all_tasks и возвращает список задач.
    """
    fake_tasks = [
        {"id": "1"},
        {"id": "2"},
    ]

    with patch("services.tasks_service.get_all_tasks", new_callable=AsyncMock) as mock:
        mock.return_value = fake_tasks

        result = await get_tasks(user_id=42)

        mock.assert_awaited_once_with(42)
        assert result == fake_tasks


# get_nearest_user_task
@pytest.mark.asyncio
async def test_get_nearest_user_task():
    """
    Проверяет получение ближайшей задачи пользователя.

    Сервис должен:
    - вызвать get_nearest_task;
    - вернуть полученную задачу (или None).
    """
    fake_task = {"id": "nearest"}

    with patch("services.tasks_service.get_nearest_task", new_callable=AsyncMock) as mock:
        mock.return_value = fake_task

        result = await get_nearest_user_task(user_id=7)

        mock.assert_awaited_once_with(7)
        assert result == fake_task


# complete_task
@pytest.mark.asyncio
async def test_complete_task():
    """
    Проверяет завершение задачи.

    Сервис не возвращает значение,
    а лишь вызывает mark_task_done с task_id.
    """
    with patch("services.tasks_service.mark_task_done", new_callable=AsyncMock) as mock:
        await complete_task("task-id")

        mock.assert_awaited_once_with("task-id")
