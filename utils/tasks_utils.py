from datetime import datetime, timedelta, timezone
from constants.time_constants import MOSCOW_TZ, RU_DAYS, RU_MONTHS
from app.logger import logger


def parse_datetime(text: str):
    text = text.strip().lower()
    now = datetime.now(MOSCOW_TZ)
    logger.debug('Запуск парсинга даты')

    # 1. Строгий формат (оставляем!)
    try:
        logger.debug('Парсинг даты прошёл успешно')
        return datetime.strptime(text, "%Y-%m-%d %H:%M")
    except ValueError:
        pass

    # 2. Сегодня / завтра
    if text.startswith("сегодня"):
        time_part = text.replace("сегодня", "").strip()
        try:
            logger.debug('Парсинг даты прошёл успешно')
            hour, minute = map(int, time_part.split(":"))
            return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        except ValueError:
            pass

    if text.startswith("завтра"):
        time_part = text.replace("завтра", "").strip()
        try:
            logger.info('Парсинг даты прошёл успешно')
            hour, minute = map(int, time_part.split(":"))
            return (now + timedelta(days=1)).replace(
                hour=hour, minute=minute, second=0, microsecond=0
            )
        except ValueError:
            pass

    logger.debug('Парсинг даты %s прошёл неуспешно', text)
    return None


def format_task_date(dt_or_str) -> str:
    """
    Преобразует datetime или ISO-строку в читаемый формат на русском:
    Например: datetime -> "Суббота, 01 Октября 2222 10:00"
    """
    if isinstance(dt_or_str, str):
        dt = datetime.fromisoformat(dt_or_str.replace("Z", "+00:00"))
    elif isinstance(dt_or_str, datetime):
        dt = dt_or_str
    else:
        logger.error("Ошибка при попытке приобразовать datetime | ISO-строку %s", dt_or_str)
        raise TypeError(f"Expected str or datetime, got {type(dt_or_str)}")

    # Приводим к московскому времени
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt_local = dt.astimezone(MOSCOW_TZ)

    day_name = RU_DAYS[dt_local.weekday()]
    month_name = RU_MONTHS[dt_local.month - 1]

    return (
        f"{day_name}, {dt_local.day:02d} {month_name} "
        f"{dt_local.year} {dt_local.hour:02d}:{dt_local.minute:02d}"
    )


def format_task(task: dict) -> str:
    """Форматирует задачу для показа пользователю"""
    date_str = format_task_date(task["scheduled_time"])
    return f"📝 {task['title']}\n⏰ {date_str}"


def parse_and_validate_datetime(text: str) -> datetime | None:
    """
    Парсит дату из текста и проверяет, что она в будущем.
    Возвращает datetime в UTC или None при ошибке.
    """
    logger.debug('Парсинг и валидация даты, введённой пользователем...')
    dt = parse_datetime(text)
    if not dt:
        logger.debug('Парсинг и валидация даты завершились неуспешно')
        return None

    dt_utc = dt.replace(tzinfo=MOSCOW_TZ).astimezone(timezone.utc)
    if dt_utc < datetime.now(timezone.utc):
        logger.debug('Парсинг даты завершился успешно, валидация не пройдена')
        return None
    logger.debug('Парсинг и валидация даты завершились успешно')
    return dt_utc
