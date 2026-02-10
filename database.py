import os
import asyncpg
from datetime import datetime
from typing import Optional, List, Dict

from app.logger import logger

# Настройка подключения к базе данных

# Получаем URL базы данных из переменной окружения
DATABASE_URL = os.getenv("DATABASE_URL")

# Проверка, что переменная окружения установлена
# Если DATABASE_URL пустой, логируем ошибку и возбуждаем исключение
if not DATABASE_URL:
    logger.error("Ошибка доступа к БД %s", DATABASE_URL)
    raise RuntimeError("DATABASE_URL is not set")

# Пул соединений с базой данных

# Хранение пула соединений в глобальной переменной
# Изначально None, будет инициализирован в init_db()
_pool: asyncpg.pool.Pool | None = None


def get_pool() -> asyncpg.Pool:
    """
    Возвращает глобальный пул соединений с базой данных.
    Проверяется, что пул уже инициализирован. Если нет, логируем ошибку
    и возбуждаем исключение.

    Returns:
        asyncpg.Pool: Пул соединений с базой данных

    Raises:
        RuntimeError: если пул соединений еще не создан
    """
    if _pool is None:
        logger.error("Ошибка инициализации пула соединений с %s", DATABASE_URL)
        raise RuntimeError("DB pool not initialized")
    return _pool


async def init_db() -> None:
    """
    Инициализация базы данных и создание необходимых таблиц.

    Шаги:
    1. Проверяем, что глобальный пул соединений _pool ещё не создан
    2. Создаем пул соединений с минимальным размером 2 и максимальным 5,
       с таймаутом 10 секунд для операций с соединением
    3. С помощью пула соединений получаем отдельное соединение
    4. Создаем таблицу tasks, если она ещё не существует
       - id: PRIMARY KEY, текстовый идентификатор задачи
       - user_id: BIGINT, ID пользователя
       - title: текстовое название задачи
       - scheduled_time: TIMESTAMPTZ, дата и время задачи
       - status: текстовый статус задачи
    5. Создаем таблицу users, если она ещё не существует
       - user_id: PRIMARY KEY, BIGINT
       - city: город пользователя (текст)

    Returns:
        None
    """
    global _pool
    if _pool is None:
        logger.debug("Создание пула соединений с %s", DATABASE_URL)
        _pool = await asyncpg.create_pool(
            DATABASE_URL, min_size=2, max_size=5, timeout=10
        )  # type: ignore

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


# Завершение работы с базой данных
async def close_db() -> None:
    """
    Закрывает все соединения в пуле базы данных и очищает глобальную переменную _pool.

    Шаги:
    1. Проверяем, что пул существует
    2. Закрываем все соединения в пуле асинхронно
    3. Обнуляем переменную _pool
    4. Логируем завершение работы с базой

    Returns:
        None
    """
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.debug("Завершение всех соединений пула соединений с %s", DATABASE_URL)


# tasks
async def add_task(task_id: str, user_id: int, title: str, scheduled_time: datetime):
    """
    Добавляет новую задачу в базу данных.

    Функция выполняет асинхронное добавление записи в таблицу tasks
    с указанием идентификатора задачи, ID пользователя, названия задачи
    и времени выполнения. Статус новой задачи по умолчанию 'pending'.

    Шаги:
    1. Получаем соединение из пула с помощью get_pool().acquire()
    2. Выполняем SQL-запрос INSERT с параметрами
       - $1 = task_id
       - $2 = user_id
       - $3 = title
       - $4 = scheduled_time
       Статус по умолчанию 'pending'
    3. SQL-запрос выполняется асинхронно, операция не возвращает результат

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

    Функция возвращает первую задачу пользователя по дате и времени выполнения,
    которая имеет статус 'pending'. Если таких задач нет, возвращается None.

    Шаги:
    1. Получаем соединение из пула с помощью get_pool().acquire()
    2. Выполняем SQL-запрос SELECT с фильтром по user_id и status='pending'
    3. Сортируем по scheduled_time по возрастанию и берём первую запись (LIMIT 1)
    4. Если запись найдена, возвращаем её как словарь (dict)
    5. Если запись отсутствует, возвращаем None

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

    Функция возвращает список всех задач пользователя со статусом 'pending',
    отсортированных по дате и времени выполнения. Каждая задача возвращается
    в виде словаря.

    Шаги:
    1. Получаем соединение из пула с помощью get_pool().acquire()
    2. Выполняем SQL-запрос SELECT с фильтром по user_id и status='pending'
    3. Сортируем все задачи по scheduled_time по возрастанию
    4. Преобразуем каждую запись из asyncpg.Record в обычный словарь
    5. Возвращаем список словарей с задачами

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

    Функция позволяет изменить запланированное время задачи по её ID.
    При этом статус задачи автоматически переводится в 'pending',
    чтобы она снова считалась активной и планировалась для напоминания.

    Шаги:
    1. Получаем соединение из пула с помощью get_pool().acquire()
    2. Выполняем SQL-запрос UPDATE:
       - обновляем поле scheduled_time на новое время
       - устанавливаем статус задачи в 'pending'
       - фильтруем задачу по уникальному task_id
    3. SQL-запрос выполняется асинхронно, результат не возвращается

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
    Функция изменяет статус задачи на 'done', чтобы она
    больше не считалась активной и не планировалась для напоминания.

    Шаги:
    1. Получаем соединение из пула с помощью get_pool().acquire()
    2. Выполняем SQL-запрос UPDATE:
       - устанавливаем status = 'done'
       - фильтруем задачу по уникальному task_id
    3. SQL-запрос выполняется асинхронно, результат не возвращается

    Args:
        task_id (str): Уникальный идентификатор задачи

    Returns:
        None
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

    Функция ищет задачу в базе данных по task_id.
    Если задача найдена, возвращается словарь с данными.
    Если задача не найдена, возвращается None.

    Шаги:
    1. Получаем соединение из пула с помощью get_pool().acquire()
    2. Выполняем SQL-запрос SELECT:
       - фильтруем по id задачи
       - возвращаем одну запись с помощью fetchrow
    3. Если запись найдена, преобразуем её из asyncpg.Record в словарь
    4. Если запись отсутствует, возвращаем None

    Args:
        task_id (str): Уникальный идентификатор задачи

    Returns:
        Optional[Dict]: Словарь с данными задачи или None
    """
    async with get_pool().acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM tasks WHERE id = $1", task_id)
        return dict(row) if row else None


# users
async def get_user_city(user_id: int) -> Optional[str]:
    """
    Получает город пользователя по его уникальному идентификатору.

    Функция выполняет поиск пользователя в таблице users по user_id.
    Если пользователь найден, возвращается его город (поле city).
    Если пользователь отсутствует, возвращается None.

    Шаги:
    1. Получаем соединение с базой данных из пула через get_pool().acquire()
    2. Выполняем SQL-запрос SELECT city для данного user_id
    3. Если запись найдена, возвращаем значение поля 'city'
    4. Если запись отсутствует, возвращаем None

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

    Функция добавляет запись о пользователе в таблицу users или обновляет
    существующую запись, если пользователь уже есть.
    Используется конструкция ON CONFLICT для обновления поля city при конфликте по user_id.

    Шаги:
    1. Получаем соединение с базой данных из пула через get_pool().acquire()
    2. Выполняем SQL-запрос INSERT:
       - если user_id отсутствует, добавляем новую запись
       - если user_id уже существует, обновляем city на новое значение
    3. SQL-запрос выполняется асинхронно, результат не возвращается

    Args:
        user_id (int): Уникальный идентификатор пользователя
        city (str): Название города для пользователя

    Returns:
        None
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

    Функция извлекает из таблицы tasks задачи, которые:
    - имеют статус 'pending' (т.е. ещё не выполнены)
    - запланированы на время позже текущего момента (CURRENT_TIMESTAMP)

    Шаги:
    1. Получаем соединение с базой данных из пула через get_pool().acquire()
    2. Выполняем SQL-запрос SELECT для извлечения всех задач с условиями:
       - status = 'pending'
       - scheduled_time > текущее время
    3. Преобразуем каждый результат fetch в словарь и формируем список
    4. Возвращаем список словарей с будущими задачами

    Args:
        -

    Returns:
        list[dict]: Список словарей с информацией о будущих задачах
    """
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


async def get_all_pending_tasks() -> list[dict]:
    """
    Возвращает все задачи со статусом 'pending' для всех пользователей.

    Эта функция используется для формирования списка напоминаний или
    обработки всех активных задач в системе.

    Шаги:
    1. Получаем соединение с базой данных из пула через get_pool().acquire()
    2. Выполняем SQL-запрос SELECT для извлечения всех задач со статусом 'pending'
    3. Преобразуем каждый результат fetch в словарь
    4. Возвращаем список словарей с задачами

    Args:
        -

    Returns:
        list[dict]: Список словарей с активными задачами
    """
    async with get_pool().acquire() as conn:
        rows = await conn.fetch("SELECT * FROM tasks WHERE status='pending'")
        return [dict(r) for r in rows]
