import os
import asyncpg
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional, List, Dict

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

pool: Optional[asyncpg.pool.Pool] = None

async def init_db() -> None:
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(DATABASE_URL)  # type: ignore

    async with pool.acquire() as conn:
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
    global pool
    if pool:
        await pool.close()
        pool = None


# ================== TASKS ==================
async def add_task(task_id: str, user_id: int, title: str, scheduled_time: datetime):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO tasks (id, user_id, title, scheduled_time, status)
            VALUES ($1, $2, $3, $4, 'pending')
            """,
            task_id, user_id, title, scheduled_time
        )


async def get_nearest_task(user_id: int) -> Optional[Dict]:
    async with pool.acquire() as conn:
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
    async with pool.acquire() as conn:
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
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE tasks
            SET scheduled_time = $1, status = 'pending'
            WHERE id = $2
            """,
            new_time, task_id
        )


async def mark_task_done(task_id: str):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE tasks
            SET status = 'done'
            WHERE id = $1
            """,
            task_id
        )


async def get_task_by_id(task_id: str) -> Optional[Dict]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM tasks WHERE id = $1",
            task_id
        )
        return dict(row) if row else None


# ================== USERS ==================
async def get_user_city(user_id: int) -> Optional[str]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT city FROM users WHERE user_id = $1",
            user_id
        )
        return row["city"] if row else None


async def set_user_city(user_id: int, city: str):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (user_id, city)
            VALUES ($1, $2)
            ON CONFLICT (user_id)
            DO UPDATE SET city = EXCLUDED.city
            """,
            user_id, city
        )
