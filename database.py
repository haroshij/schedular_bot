import os
import asyncpg
from urllib.parse import urlparse
from datetime import datetime
from typing import Optional, List, Dict

from app.logger import logger

DATABASE_URL = os.getenv("DATABASE_URL")

# Парсим наш URL, и создаём безопасный URL, чтобы показывать в логах
parsed = urlparse(DATABASE_URL)
safe_url = f"{parsed.scheme}://*****@{parsed.hostname}:{parsed.port}/{parsed.path}"

if not DATABASE_URL:
    logger.error("Ошибка доступа к БД %s", safe_url)
    raise RuntimeError("DATABASE_URL is not set")

_pool: asyncpg.pool.Pool | None = None  # Пул соединений с базой данных


def get_pool() -> asyncpg.Pool:
    """
    Возвращает глобальный пул соединений с базой данных.

    Returns:
        asyncpg.Pool: Пул соединений с базой данных

    Raises:
        RuntimeError: если пул соединений ещё не создан
    """
    if _pool is None:
        logger.error("Ошибка инициализации пула соединений с %s", safe_url)
        raise RuntimeError("DB pool not initialized")
    return _pool


async def init_db() -> None:
    """
    Инициализация базы данных и создание необходимых таблиц.
    """
    global _pool
    if _pool is None:
        logger.debug("Создание пула соединений с %s", safe_url)
        _pool = await asyncpg.create_pool(  # type: ignore
            DATABASE_URL, min_size=2, max_size=5, timeout=10
        )

    # Получаем соединение из пула для создания таблиц
    async with get_pool().acquire() as conn:
        # Создание таблицы задач
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            title TEXT NOT NULL,
            scheduled_time TIMESTAMPTZ NOT NULL,
            status TEXT NOT NULL
        )
        """)

        # Создание таблицы пользователей
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            city TEXT
        )
        """)


async def close_db() -> None:
    """
    Закрывает все соединения в пуле базы данных и очищает глобальную переменную _pool.
    """
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.debug("Завершение всех соединений пула соединений с %s", DATABASE_URL)


async def add_task(task_id: str, user_id: int, title: str, scheduled_time: datetime):
    """
    Добавляет новую задачу в базу данных.

    Args:
        task_id (str): Уникальный идентификатор задачи
        user_id (int): Идентификатор пользователя, которому принадлежит задача
        title (str): Название задачи
        scheduled_time (datetime): Время запланированного выполнения задачи

    Returns:
        None
    """
    async with get_pool().acquire() as conn:
        await conn.execute(
            """
            INSERT INTO tasks (id, user_id, title, scheduled_time, status)
            VALUES ($1, $2, $3, $4, 'pending')
            """,
            task_id,
            user_id,
            title,
            scheduled_time,
        )


async def get_nearest_task(user_id: int) -> Optional[Dict]:
    """
    Получает ближайшую запланированную (pending) задачу пользователя.

    Args:
        user_id (int): Идентификатор пользователя

    Returns:
        Optional[Dict]: Словарь с данными ближайшей задачи или None
    """
    async with get_pool().acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT * FROM tasks
            WHERE user_id = $1 AND status = 'pending'
            ORDER BY scheduled_time
            LIMIT 1
            """,
            user_id,
        )
        return dict(row) if row else None


async def get_all_tasks(user_id: int) -> List[Dict]:
    """
    Получает все запланированные (pending) задачи пользователя.

    Args:
        user_id (int): Идентификатор пользователя

    Returns:
        List[Dict]: Список словарей с данными всех запланированных задач
    """
    async with get_pool().acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT * FROM tasks
            WHERE user_id = $1 AND status = 'pending'
            ORDER BY scheduled_time
            """,
            user_id,
        )
        return [dict(r) for r in rows]


async def update_task_time(task_id: str, new_time: datetime):
    """
    Обновляет время выполнения задачи и устанавливает статус 'pending'.

    Args:
        task_id (str): Уникальный идентификатор задачи
        new_time (datetime): Новое время выполнения задачи

    Returns:
        None
    """
    async with get_pool().acquire() as conn:
        await conn.execute(
            """
            UPDATE tasks
            SET scheduled_time = $1, status = 'pending'
            WHERE id = $2
            """,
            new_time,
            task_id,
        )


async def mark_task_done(task_id: str):
    """
    Помечает задачу как выполненную.

    Args:
        task_id (str): Уникальный идентификатор задачи
    """
    async with get_pool().acquire() as conn:
        await conn.execute(
            """
            UPDATE tasks
            SET status = 'done'
            WHERE id = $1
            """,
            task_id,
        )


async def get_task_by_id(task_id: str) -> Optional[Dict]:
    """
    Получает задачу по её уникальному идентификатору.

    Args:
        task_id (str): Уникальный идентификатор задачи

    Returns:
        Optional[Dict]: Словарь с данными задачи или None
    """
    async with get_pool().acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM tasks WHERE id = $1", task_id)
        return dict(row) if row else None


async def get_user_city(user_id: int) -> Optional[str]:
    """
    Получает город пользователя по его уникальному идентификатору.

    Args:
        user_id (int): Уникальный идентификатор пользователя

    Returns:
        Optional[str]: Название города пользователя или None
    """
    async with get_pool().acquire() as conn:
        row = await conn.fetchrow("SELECT city FROM users WHERE user_id = $1", user_id)
        return row["city"] if row else None


async def set_user_city(user_id: int, city: str):
    """
    Устанавливает или обновляет город пользователя в базе данных.
    """
    async with get_pool().acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (user_id, city)
            VALUES ($1, $2)
            ON CONFLICT (user_id)
            DO UPDATE SET city = EXCLUDED.city
            """,
            user_id,
            city,
        )


# ПОКА НЕ ИСПОЛЬЗУЕТСЯ
async def get_future_tasks() -> list[dict]:
    """
    Возвращает список всех будущих задач со статусом 'pending'.

    Returns:
        list[dict]: Список словарей с информацией о будущих задачах
    """
    async with get_pool().acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM tasks
            WHERE status = 'pending'
              AND scheduled_time > CURRENT_TIMESTAMP
            """
        )
        return [dict(r) for r in rows]


async def get_all_pending_tasks() -> list[dict]:
    """
    Возвращает все задачи со статусом 'pending' для всех пользователей.

    Returns:
        list[dict]: Список словарей с активными задачами
    """
    async with get_pool().acquire() as conn:
        rows = await conn.fetch("SELECT * FROM tasks WHERE status='pending'")
        return [dict(r) for r in rows]
