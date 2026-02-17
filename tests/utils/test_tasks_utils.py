import pytest
from datetime import datetime, timezone, timedelta
from freezegun import freeze_time
from utils.tasks_utils import (
    parse_datetime,
    format_task_date,
    format_task,
    parse_and_validate_datetime,
)
from constants.time_constants import MOSCOW_TZ, RU_DAYS, RU_MONTHS


@freeze_time("2026-02-09 12:00:00", tz_offset=3)
@pytest.mark.parametrize(
    "text,expected",
    [
        ("2026-02-10 15:30", datetime(2026, 2, 10, 15, 30)),
        ("сегодня 14:45", datetime(2026, 2, 9, 14, 45, tzinfo=MOSCOW_TZ)),
        ("завтра 09:15", datetime(2026, 2, 10, 9, 15, tzinfo=MOSCOW_TZ)),
        (
            "  сегодня  07:00  ",
            datetime(2026, 2, 9, 7, 0, tzinfo=MOSCOW_TZ),
        ),  # с пробелами
        ("некорректно", None),
        ("сегодня abc", None),
        ("завтра 25:00", None),
    ],
)
def test_parse_datetime(text, expected):
    """
    Тестирование функции parse_datetime.
    """

    dt = parse_datetime(text)
    assert dt == expected


@freeze_time("2026-02-09 12:00:00", tz_offset=3)
def test_format_task_date_datetime():
    """
    Тестирование функции format_task_date с объектом datetime.
    """

    # Создаем datetime с tzinfo=UTC
    dt = datetime(2026, 2, 9, 15, 30, tzinfo=timezone.utc)

    result = format_task_date(dt)
    day_name = RU_DAYS[dt.astimezone(MOSCOW_TZ).weekday()]
    month_name = RU_MONTHS[dt.astimezone(MOSCOW_TZ).month - 1]

    # Формируем ожидаемую строку с учетом преобразования времени UTC->Moscow (15:30+3=18:30)
    expected = f"{day_name}, 09 {month_name} 2026 18:30"

    assert result == expected


def test_format_task_date_iso_string():
    """
    Тестирование функции format_task_date с ISO-строкой.
    """

    # ISO-строка с UTC временем
    iso_str = "2026-02-10T12:00:00Z"

    # Вызываем функцию для форматирования
    result = format_task_date(iso_str)

    # Преобразуем ISO-строку в datetime и переводим в Московское время
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00")).astimezone(MOSCOW_TZ)

    day_name = RU_DAYS[dt.weekday()]
    month_name = RU_MONTHS[dt.month - 1]

    # Формируем ожидаемую строку с учетом перевода UTC->Moscow (12:00+3=15:00)
    expected = f"{day_name}, 10 {month_name} 2026 15:00"

    # Проверяем совпадение результата функции с ожидаемым
    assert result == expected


def test_format_task_date_invalid_type():
    """
    Проверка обработки некорректного типа аргумента в format_task_date.
    """

    # Проверяем, что передача int вызывает TypeError
    with pytest.raises(TypeError):
        format_task_date(12345)  # type: ignore


def test_format_task():
    """
    Проверка форматирования задачи для отображения пользователю.
    """

    task = {
        "title": "Тестовая задача",
        "scheduled_time": datetime(2026, 2, 10, 12, 0, tzinfo=timezone.utc),
    }

    result = format_task(task)
    date_str = format_task_date(task["scheduled_time"])

    assert result == f"📝 {task['title']}\n⏰ {date_str}"


def test_format_task_date_naive_datetime():
    """
    Проверка форматирования "наивного" datetime (без tzinfo) в format_task_date.
    """

    dt = datetime(2026, 2, 9, 12, 0)  # нет tzinfo
    result = format_task_date(dt)
    expected_hour = (dt.replace(tzinfo=timezone.utc).astimezone(MOSCOW_TZ)).hour

    # Проверяем, что час с учетом UTC+3 присутствует в отформатированной строке
    assert str(expected_hour).zfill(2) in result


@pytest.mark.parametrize(
    "text,expected",
    [
        # Тестируем корректное значение "завтра 14:00"
        # Ожидается, что функция вернет datetime в UTC на следующий день
        (
            "завтра 14:00",
            (datetime.now() + timedelta(days=1)).replace(
                day=datetime.now().day + 1,  # день завтрашний
                hour=11,  # 14:00 по Московскому времени = 11:00 UTC
                minute=0,
                second=0,
                microsecond=0,
                tzinfo=timezone.utc,
            ),
        ),
        # Тестируем корректное значение "сегодня 23:59"
        # Ожидается, что функция вернет datetime в UTC текущего дня
        (
            "сегодня 23:59",
            datetime.now().replace(
                hour=20,  # 23:59 по Московскому времени = 20:59 UTC
                minute=59,
                second=0,
                microsecond=0,
                tzinfo=timezone.utc,
            ),
        ),
        # Тестируем дату в прошлом
        # Ожидается, что функция вернет None, так как дата уже прошла
        ("2026-02-08 15:00", None),
        # Тестируем некорректный формат строки
        # Ожидается, что функция вернет None
        ("некорректно", None),
    ],
)
def test_parse_and_validate_datetime(text, expected):
    """
    Проверка работы функции parse_and_validate_datetime.
    """

    dt_utc = parse_and_validate_datetime(text)
    assert dt_utc == expected
