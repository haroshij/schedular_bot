from datetime import datetime, timedelta, timezone
from constants.time_constants import MOSCOW_TZ, RU_DAYS, RU_MONTHS
from app.logger import logger


def parse_datetime(text: str):
    """
    Парсинг даты и времени из пользовательского ввода.

    Args:
        text (str): Строка с датой и временем, введённая пользователем.

    Returns:
        datetime | None: Объект datetime в московском часовом поясе
        при успешном парсинге или None при ошибке.
    """

    text = text.strip().lower()
    now = datetime.now(MOSCOW_TZ)
    logger.debug("Запуск парсинга даты")

    # 1. Строгий формат: YYYY-MM-DD HH:MM
    try:
        logger.debug("Парсинг даты прошёл успешно")
        return datetime.strptime(text, "%Y-%m-%d %H:%M")
    except ValueError:
        pass

    # 2. Относительная дата: "сегодня HH:MM"
    if text.startswith("сегодня"):
        time_part = text.replace("сегодня", "").strip()
        try:
            hour, minute = map(int, time_part.split(":"))
            logger.debug("Парсинг даты прошёл успешно")
            return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        except ValueError:
            pass

    # 3. Относительная дата: "завтра HH:MM"
    if text.startswith("завтра"):
        time_part = text.replace("завтра", "").strip()
        try:
            hour, minute = map(int, time_part.split(":"))
            logger.info("Парсинг даты прошёл успешно")

            return (now + timedelta(days=1)).replace(
                hour=hour, minute=minute, second=0, microsecond=0
            )
        except ValueError:
            pass

    logger.debug("Парсинг даты %s прошёл неуспешно", text)
    return None


def format_task_date(dt_or_str) -> str:
    """
    Преобразует дату задачи в читаемый формат на русском языке.

    Args:
        dt_or_str (datetime | str): Дата задачи в виде datetime
        или строки в ISO-формате.

    Returns:
        str: Отформатированная строка с датой и временем задачи.

    Raises:
        TypeError: Если передан аргумент неподдерживаемого типа.
    """
    # Если дата пришла в виде строки — пытаемся распарсить ISO-формат
    if isinstance(dt_or_str, str):
        dt = datetime.fromisoformat(dt_or_str.replace("Z", "+00:00"))
    elif isinstance(dt_or_str, datetime):
        dt = dt_or_str
    else:
        logger.error(
            "Ошибка при попытке приобразовать datetime | ISO-строку %s", dt_or_str
        )
        raise TypeError(f"Expected str or datetime, got {type(dt_or_str)}")

    if dt.tzinfo is None:  # Если tzinfo отсутствует — считаем дату UTC
        dt = dt.replace(tzinfo=timezone.utc)

    dt_local = dt.astimezone(MOSCOW_TZ)  # Конвертируем дату во временную зону Москвы
    day_name = RU_DAYS[dt_local.weekday()]
    month_name = RU_MONTHS[dt_local.month - 1]

    return (
        f"{day_name}, {dt_local.day:02d} {month_name} "
        f"{dt_local.year} {dt_local.hour:02d}:{dt_local.minute:02d}"
    )


def format_task(task: dict) -> str:
    """
    Форматирует задачу для отображения пользователю в сообщении Telegram.

    Args:
        task (dict): Словарь задачи, содержащий как минимум
        ключи 'title' и 'scheduled_time'.

    Returns:
        str: Готовая строка для отправки пользователю.
    """

    date_str = format_task_date(task["scheduled_time"])

    return f"📝 {task['title']}\n⏰ {date_str}"


def parse_and_validate_datetime(text: str) -> datetime | None:
    """
    Парсит дату из пользовательского ввода и проверяет,
    что она находится в будущем.

    Args:
        text (str): Строка с датой и временем, введённая пользователем.

    Returns:
        datetime | None: Объект datetime в UTC при успешном парсинге
        и валидации или None, если дата некорректна или уже прошла.
    """

    logger.debug("Парсинг и валидация даты, введённой пользователем...")
    dt = parse_datetime(text)

    if not dt:
        logger.debug("Парсинг и валидация даты завершились неуспешно")
        return None

    # Приводим дату к UTC для дальнейшей унифицированной работы
    dt_utc = dt.replace(tzinfo=MOSCOW_TZ).astimezone(timezone.utc)

    # Проверяем, что дата находится в будущем
    if dt_utc < datetime.now(timezone.utc):
        logger.debug("Парсинг даты завершился успешно, валидация не пройдена")
        return None

    logger.debug("Парсинг и валидация даты завершились успешно")
    return dt_utc
