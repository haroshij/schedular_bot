import os
import asyncpg
from datetime import datetime
from typing import Optional, List, Dict

from app.logger import logger

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("Ошибка доступа к БД %s", DATABASE_URL)
    raise RuntimeError("DATABASE_URL is not set")

_pool: asyncpg.pool.Pool | None = None

def get_pool() -> asyncpg.Pool:
    if _pool is None:
        logger.error('Ошибка инициализации пула соединений с %s', DATABASE_URL)
        raise RuntimeError("DB pool not initialized")
    return _pool

async def init_db() -> None:
    global _pool
    if _pool is None:
        logger.debug("Создание пула соединений с %s", DATABASE_URL)
        _pool = await asyncpg.create_pool(DATABASE_URL,min_size=2, max_size=5, timeout=10)  # type: ignore

    async with get_pool().acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            title TEXT NOT NULL,
            scheduled_time TIMESTAMPTZ NOT NULL,
            status TEXT NOT NULL
        )
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            city TEXT
        )
        """)


# ---------------- CLOSE ----------------
async def close_db() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.debug("Завершение всех соединений пула соединений с %s", DATABASE_URL)


# ================== TASKS ==================
async def add_task(task_id: str, user_id: int, title: str, scheduled_time: datetime):
    async with get_pool().acquire() as conn:
        await conn.execute(
            """
            INSERT INTO tasks (id, user_id, title, scheduled_time, status)
            VALUES ($1, $2, $3, $4, 'pending')
            """,
            task_id, user_id, title, scheduled_time
        )


async def get_nearest_task(user_id: int) -> Optional[Dict]:
    async with get_pool().acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT * FROM tasks
            WHERE user_id = $1 AND status = 'pending'
            ORDER BY scheduled_time
            LIMIT 1
            """,
            user_id
        )
        return dict(row) if row else None


async def get_all_tasks(user_id: int) -> List[Dict]:
    async with get_pool().acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT * FROM tasks
            WHERE user_id = $1 AND status = 'pending'
            ORDER BY scheduled_time
            """,
            user_id
        )
        return [dict(r) for r in rows]


async def update_task_time(task_id: str, new_time: datetime):
    async with get_pool().acquire() as conn:
        await conn.execute(
            """
            UPDATE tasks
            SET scheduled_time = $1, status = 'pending'
            WHERE id = $2
            """,
            new_time, task_id
        )


async def mark_task_done(task_id: str):
    async with get_pool().acquire() as conn:
        await conn.execute(
            """
            UPDATE tasks
            SET status = 'done'
            WHERE id = $1
            """,
            task_id
        )


async def get_task_by_id(task_id: str) -> Optional[Dict]:
    async with get_pool().acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM tasks WHERE id = $1",
            task_id
        )
        return dict(row) if row else None


# ================== USERS ==================
async def get_user_city(user_id: int) -> Optional[str]:
    async with get_pool().acquire() as conn:
        row = await conn.fetchrow(
            "SELECT city FROM users WHERE user_id = $1",
            user_id
        )
        return row["city"] if row else None


async def set_user_city(user_id: int, city: str):
    async with get_pool().acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (user_id, city)
            VALUES ($1, $2)
            ON CONFLICT (user_id)
            DO UPDATE SET city = EXCLUDED.city
            """,
            user_id, city
        )

# ПОКА НЕ ИСПОЛЬЗУЕТСЯ
async def get_future_tasks() -> list[dict]:
    async with get_pool().acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM tasks
            WHERE status = 'pending'  -- берем только невыполненные
              AND scheduled_time > CURRENT_TIMESTAMP
            """
        )
        return [dict(r) for r in rows]


# Возвращает все pending задачи для всех пользователей (необходимо для формирвоания списка напоминаний)
async def get_all_pending_tasks() -> list[dict]:
    async with get_pool().acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM tasks WHERE status='pending'"
        )
        return [dict(r) for r in rows]
