from datetime import datetime, timezone

from telegram import Update
from telegram.ext import CallbackContext

from keyboard import MAIN_MENU
from states import ADD_DATE, ADD_TEXT, POSTPONE_DATE, END
from bot.jobs import send_task_reminder
from handlers.common.common import cancel_menu_kb
from services.tasks_service import create_task, change_task_time
from utils.tasks_utils import parse_and_validate_datetime
from app.decorators import log_handler
from app.logger import logger


# Ввод даты новой задачи
@log_handler
async def add_task_date(update: Update, context: CallbackContext):
    """
    Обрабатывает ввод даты и времени для новой задачи.
    Функция проверяет корректность введённой даты, преобразует её
    в UTC и сохраняет во временных данных пользователя для
    последующего ввода текста задачи. Если дата некорректна
    или уже прошла, пользователь остаётся в состоянии ADD_DATE.

    Args:
        update (Update): Объект обновления Telegram с сообщением пользователя.
        context (CallbackContext): Контекст с временными данными пользователя.

    Returns:
        str: Константа состояния ADD_TEXT для перехода к вводу текста
             или ADD_DATE при некорректном вводе.
    """
    # Парсим и проверяем дату и время
    dt_utc = parse_and_validate_datetime(update.message.text)

    if not dt_utc:
        await update.message.reply_text(
            "❌ Неверный формат или устаревшая дата. Попробуйте снова:\n\n"
            "Примеры:\n"
            "• 2026-02-10 18:30\n"
            "• сегодня 21:00\n"
            "• завтра 9:00",
            reply_markup=cancel_menu_kb(),
        )

        logger.info(
            "Пользователь %s ввёл неверный формат или устаревшую дату: %s",
            update.effective_user.id,
            update.message.text,
        )
        return ADD_DATE  # Остаёмся в состоянии ввода даты

    # Сохраняем корректную дату во временных данных пользователя
    context.user_data["task_time"] = dt_utc

    # Просим пользователя ввести текст задачи после успешного ввода даты
    await update.message.reply_text(
        "Теперь введи текст задачи:", reply_markup=cancel_menu_kb()
    )
    return ADD_TEXT  # Переход к следующему шагу — ввод текста задачи


@log_handler
async def add_task_text(update: Update, context: CallbackContext):
    """
    Обрабатывает ввод текста новой задачи.
    Функция создаёт задачу в БД с ранее введённой датой.
    Также добавляет задание в job_queue для напоминания.

    Args:
        update (Update): Объект обновления Telegram с сообщением пользователя.
        context (CallbackContext): Контекст с временными данными пользователя и job_queue.

    Returns:
        str: ConversationHandler.END при успешном добавлении задачи
             или при некорректной дате.
    """

    user_id = update.effective_user.id
    title = update.message.text
    scheduled_time = context.user_data["task_time"]

    now = datetime.now(timezone.utc)
    if scheduled_time < now:
        await update.message.reply_text(
            "❌ Введённая дата уже прошла. Задача не добавлена. Пожалуйста, попробуйте снова",
            reply_markup=MAIN_MENU,
        )

        logger.info("Пользователь %s ввёл устаревшую дату: %s", user_id, scheduled_time)
        context.user_data.clear()
        return END

    task = await create_task(user_id, title, scheduled_time)

    delay = (task["scheduled_time"] - datetime.now(timezone.utc)).total_seconds()

    # Добавляем напоминание в job_queue
    context.application.job_queue.run_once(
        send_task_reminder,
        max(0, delay),
        data={"task": task, "chat_id": user_id},
        name=f"task_{task['id']}",
    )

    await update.message.reply_text("✅ Задача добавлена", reply_markup=MAIN_MENU)
    context.user_data.clear()
    return END


@log_handler
async def postpone_date(update: Update, context: CallbackContext):
    """
    Обрабатывает перенос даты существующей задачи.

    Args:
        update (Update): Объект обновления Telegram с сообщением пользователя.
        context (CallbackContext): Контекст с временными данными пользователя и job_queue.

    Returns:
        str: ConversationHandler.END после успешного переноса
             или POSTPONE_DATE при некорректном вводе.
    """

    dt_utc = parse_and_validate_datetime(update.message.text)
    if not dt_utc:
        await update.message.reply_text(
            "❌ Неверный формат или устаревшая дата. Попробуйте снова:\n\n"
            "Примеры:\n"
            "• 2026-02-10 18:30\n"
            "• сегодня 21:00\n"
            "• завтра 9:00",
            reply_markup=cancel_menu_kb(),
        )
        logger.warning(
            "Пользователь %s ввёл неверный формат или устаревшую дату: %s",
            update.effective_user.id,
            update.message.text,
        )
        return POSTPONE_DATE  # Остаёмся в состоянии переноса

    task_id = context.user_data["task_id"]

    task = await change_task_time(task_id, dt_utc)

    for job in context.application.job_queue.jobs():
        if job.name == f"task_{task_id}":
            job.schedule_removal()
            break

    delay = (task["scheduled_time"] - datetime.now(timezone.utc)).total_seconds()
    context.application.job_queue.run_once(
        send_task_reminder,
        max(0, delay),
        data={"task": task, "chat_id": task["user_id"]},
        name=f"task_{task_id}",
    )

    await update.message.reply_text("⏳ Время изменено", reply_markup=MAIN_MENU)
    return END
