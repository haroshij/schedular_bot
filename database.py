import aiosqlite
from datetime import datetime
from typing import Optional, List, Dict

DB_NAME = "tasks.db"


# ---------- Init ----------
async def init_db():
    async with aiosqlite.connect(DB_NAME) as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            scheduled_time TEXT NOT NULL,
            status TEXT NOT NULL
        )
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            city TEXT
        )
        """)

        await conn.commit()


# ---------- Tasks ----------
async def add_task(task_id: str, user_id: int, title: str, scheduled_time: datetime):
    async with aiosqlite.connect(DB_NAME) as conn:
        await conn.execute(
            """
            INSERT INTO tasks (id, user_id, title, scheduled_time, status)
            VALUES (?, ?, ?, ?, 'pending')
            """,
            (task_id, user_id, title, scheduled_time.isoformat())
        )
        await conn.commit()


async def get_nearest_task(user_id: int) -> Optional[Dict]:
    async with aiosqlite.connect(DB_NAME) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute(
            """
            SELECT * FROM tasks
            WHERE user_id = ?
              AND status = 'pending'
            ORDER BY scheduled_time
            LIMIT 1
            """,
            (user_id,)
        )
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_all_tasks(user_id: int) -> List[Dict]:
    async with aiosqlite.connect(DB_NAME) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute(
            """
            SELECT * FROM tasks
            WHERE user_id = ?
               AND status = 'pending'
            ORDER BY scheduled_time
            """,
            (user_id,)
        )
        rows = await cur.fetchall()
        return [dict(row) for row in rows]


async def update_task_time(task_id: str, new_time: datetime):
    async with aiosqlite.connect(DB_NAME) as conn:
        await conn.execute(
            """
            UPDATE tasks
            SET scheduled_time = ?, status = 'pending'
            WHERE id = ?
            """,
            (new_time.isoformat(), task_id)
        )
        await conn.commit()


async def mark_task_done(task_id: str):
    async with aiosqlite.connect(DB_NAME) as conn:
        await conn.execute(
            """
            UPDATE tasks
            SET status = 'done'
            WHERE id = ?
            """,
            (task_id,)
        )
        await conn.commit()


# ---------- Users ----------
async def get_user_city(user_id: int) -> str | None:
    async with aiosqlite.connect(DB_NAME) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute(
            "SELECT city FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = await cur.fetchone()
        return row["city"] if row else None


async def set_user_city(user_id: int, city: str):
    async with aiosqlite.connect(DB_NAME) as conn:
        await conn.execute(
            """
            INSERT INTO users (user_id, city)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET city = excluded.city
            """,
            (user_id, city)
        )
        await conn.commit()

async def get_task_by_id(task_id: str) -> dict | None:
    async with aiosqlite.connect(DB_NAME) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = await cur.fetchone()
        return dict(row) if row else None
