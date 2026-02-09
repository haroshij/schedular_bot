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
from handlers.common import start, cancel
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
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN not set")

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

    # ---------- COMMANDS ----------
    app.add_handler(CommandHandler("start", start))

    # ---------- ADD TASK ----------
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
            # fallback добавляем для кнопок "Отмена" и "В меню"
            fallbacks=[
                CommandHandler("cancel", cancel),
                CallbackQueryHandler(cancel, pattern="^cancel$"),
                CallbackQueryHandler(cancel, pattern="^menu$"),
            ],
        )
    )

    # ---------- POSTPONE ----------
    app.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(callbacks, pattern="^postpone:")],
            states={
                POSTPONE_DATE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, postpone_date)
                ]
            },
            fallbacks=[
                CommandHandler("cancel", cancel),
                CallbackQueryHandler(cancel, pattern="^cancel$"),
                CallbackQueryHandler(cancel, pattern="^menu$"),
            ],
        )
    )

    # ---------- SEARCH ----------
    app.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(callbacks, pattern="^search$")],
            states={
                SEARCH_QUERY: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler)
                ]
            },
            fallbacks=[
                CommandHandler("cancel", cancel),
                CallbackQueryHandler(cancel, pattern="^cancel$"),
                CallbackQueryHandler(cancel, pattern="^menu$"),
            ],
        )
    )

    # ---------- WEATHER ----------
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
                CallbackQueryHandler(cancel, pattern="^menu$"),
            ],
        )
    )

    # ---------- CALLBACKS ----------
    app.add_handler(CallbackQueryHandler(callbacks))

    return app
