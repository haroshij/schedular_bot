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
    # Парсим введённую дату и время
    dt_utc = parse_and_validate_datetime(update.message.text)

    # Проверяем, корректна ли дата
    if not dt_utc:
        # Если дата некорректна, выводим пользователю сообщение с примерами правильного формата
        await update.message.reply_text(
            "❌ Неверный формат или устаревшая дата. Попробуйте снова:\n\n"
            "Примеры:\n"
            "• 2026-02-10 18:30\n"
            "• сегодня 21:00\n"
            "• завтра 9:00",
            reply_markup=cancel_menu_kb(),  # Кнопки "Отмена" и "В меню"
        )
        # Логируем попытку некорректного ввода
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


# Ввод текста новой задачи
@log_handler
async def add_task_text(update: Update, context: CallbackContext):
    """
    Обрабатывает ввод текста новой задачи.

    Функция создаёт задачу в БД с ранее введённой датой.
    Также добавляет задание в job_queue для напоминания.
    Если введённая дата уже прошла, задача не создаётся.

    Args:
        update (Update): Объект обновления Telegram с сообщением пользователя.
        context (CallbackContext): Контекст с временными данными пользователя и job_queue.

    Returns:
        str: ConversationHandler.END при успешном добавлении задачи
             или при некорректной дате.
    """
    # Получаем ID пользователя из обновления
    user_id = update.effective_user.id
    # Получаем текст задачи
    title = update.message.text
    # Получаем дату из временных данных пользователя
    scheduled_time = context.user_data["task_time"]

    # Текущее время для проверки корректности даты
    now = datetime.now(timezone.utc)
    if scheduled_time < now:
        # Если пользователь ввёл дату в прошлом — задача не добавляется
        await update.message.reply_text(
            "❌ Введённая дата уже прошла. Задача не добавлена. Пожалуйста, попробуйте снова",
            reply_markup=MAIN_MENU,
        )

        logger.info("Пользователь %s ввёл устаревшую дату: %s", user_id, scheduled_time)
        # Очищаем временные данные пользователя
        context.user_data.clear()
        return END

    # Создаём задачу в базе данных
    task = await create_task(user_id, title, scheduled_time)

    # Рассчитываем задержку до напоминания в секундах
    delay = (task["scheduled_time"] - datetime.now(timezone.utc)).total_seconds()

    # Добавляем задание напоминания в job_queue
    context.application.job_queue.run_once(
        send_task_reminder,  # Функция, которая будет вызвана
        max(0, delay),  # Задержка до выполнения
        data={"task": task, "chat_id": user_id},  # Передаём данные для функции
        name=f"task_{task['id']}",  # Уникальное имя задания
    )

    # Подтверждаем пользователю добавление задачи
    await update.message.reply_text("✅ Задача добавлена", reply_markup=MAIN_MENU)
    # Очищаем временные данные пользователя
    context.user_data.clear()
    return END


# Перенос задачи
@log_handler
async def postpone_date(update: Update, context: CallbackContext):
    """
    Обрабатывает перенос даты существующей задачи.

    Функция проверяет корректность введённой даты, обновляет
    задачу в БД и перенастраивает job_queue для нового времени.
    Если дата некорректна или прошла, пользователь остаётся в
    состоянии POSTPONE_DATE.

    Args:
        update (Update): Объект обновления Telegram с сообщением пользователя.
        context (CallbackContext): Контекст с временными данными пользователя и job_queue.

    Returns:
        str: ConversationHandler.END после успешного переноса
             или POSTPONE_DATE при некорректном вводе.
    """
    # Парсим и проверяем новую дату из сообщения
    dt_utc = parse_and_validate_datetime(update.message.text)
    if not dt_utc:
        # Некорректная дата — показываем пользователю пример правильного формата
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

    # Получаем ID задачи из временных данных пользователя
    task_id = context.user_data["task_id"]

    # Обновляем дату задачи в базе данных
    task = await change_task_time(task_id, dt_utc)

    # Удаляем старое задание из job_queue, чтобы не сработало старое напоминание
    for job in context.application.job_queue.jobs():
        if job.name == f"task_{task_id}":
            job.schedule_removal()
            break

    # Планируем новое напоминание с новой датой
    delay = (task["scheduled_time"] - datetime.now(timezone.utc)).total_seconds()
    context.application.job_queue.run_once(
        send_task_reminder,
        max(0, delay),
        data={"task": task, "chat_id": task["user_id"]},
        name=f"task_{task_id}",
    )

    # Подтверждаем пользователю, что время задачи изменено
    await update.message.reply_text("⏳ Время изменено", reply_markup=MAIN_MENU)
    return END
