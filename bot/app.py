"""
Модуль инициализации и настройки Telegram бота.

Здесь создаётся экземпляр бота с помощью ApplicationBuilder.
Выполняются:
- Настройка токена из переменных окружения
- Инициализация базы данных при старте
- Восстановление отложенных задач
- Добавление хендлеров команд, callback и разговоров
- Логирование всех этапов работы бота
"""

import os
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)
from app.logger import logger
from database import init_db, close_db
from handlers.common.common import start, cancel
from handlers.tasks_handler import add_task_date, add_task_text, postpone_date
from handlers.search_handler import search_handler
from handlers.weather_handler import weather_handler
from handlers.callbacks.callbacks import callbacks
from bot.jobs import restore_jobs
from states import (
    ADD_DATE,
    ADD_TEXT,
    POSTPONE_DATE,
    SEARCH_QUERY,
    WEATHER_CITY,
)


def create_app():
    """Создаёт и конфигурирует экземпляр Telegram бота.

    Основные шаги:
        1. Получение токена из переменных окружения.
        2. Настройка асинхронных функций при запуске и остановке бота:
            - on_startup: инициализация БД, восстановление задач
            - on_shutdown: закрытие соединений с БД, лог остановки
        3. Создание ApplicationBuilder и установка функций startup/shutdown.
        4. Регистрация хендлеров:
            - Команды (/start)
            - Добавление задач (add_task)
            - Перенос даты задач (postpone)
            - Поиск (search)
            - Погода (weather)
            - Обработчик всех callback запросов
        5. Возврат готового объекта бота для запуска.

    Returns:
        telegram.ext.Application: Конфигурированный экземпляр бота.

    Raises:
        RuntimeError: Если TELEGRAM_TOKEN не установлен в переменных окружения.
    """
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN не установлен в переменных окружения")

    async def on_startup(app):
        logger.info("Инициализация БД...")
        await init_db()
        logger.info("Восстановление напоминаний по задачам...")
        await restore_jobs(app)

    async def on_shutdown(_):
        logger.info("Закрытие соединений с БД...")
        await close_db()
        logger.info("Бот остановлен")

    app = (
        ApplicationBuilder()
        .token(token)
        .post_init(on_startup)
        .post_shutdown(on_shutdown)
        .build()
    )

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(callbacks, pattern="^add_task$")],
            states={
                ADD_DATE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, add_task_date)
                ],
                ADD_TEXT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, add_task_text)
                ],
            },
            fallbacks=[
                CallbackQueryHandler(cancel, pattern="^cancel$"),
            ],
        )
    )

    app.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(callbacks, pattern="^postpone:")],
            states={
                POSTPONE_DATE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, postpone_date)
                ]
            },
            fallbacks=[
                CallbackQueryHandler(cancel, pattern="^cancel$"),
            ],
        )
    )

    app.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(callbacks, pattern="^search$")],
            states={
                SEARCH_QUERY: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler)
                ]
            },
            fallbacks=[
                CallbackQueryHandler(cancel, pattern="^cancel$"),
            ],
        )
    )

    app.add_handler(
        ConversationHandler(
            entry_points=[
                CallbackQueryHandler(callbacks, pattern="^weather$"),
                CallbackQueryHandler(callbacks, pattern="^weather_change$"),
            ],
            states={
                WEATHER_CITY: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, weather_handler)
                ]
            },
            fallbacks=[
                CommandHandler("cancel", cancel),
                CallbackQueryHandler(cancel, pattern="^cancel$"),
            ],
        )
    )

    # Универсальный хендлер для всех callback-запросов
    app.add_handler(CallbackQueryHandler(callbacks))

    # Возвращаем готовый объект бота
    return app
