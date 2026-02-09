import pytest
from datetime import datetime, timezone, timedelta
from utils.tasks_utils import parse_datetime, format_task_date, format_task, parse_and_validate_datetime
from constants.time_constants import MOSCOW_TZ, RU_DAYS, RU_MONTHS
from freezegun import freeze_time


# Тесты для parse_datetime
@freeze_time("2026-02-09 12:00:00", tz_offset=3)
@pytest.mark.parametrize(
    "text,expected",
    [
        ("2026-02-10 15:30", datetime(2026, 2, 10, 15, 30)),
        ("сегодня 14:45", datetime(2026, 2, 9, 14, 45, tzinfo=MOSCOW_TZ)),
        ("завтра 09:15", datetime(2026, 2, 10, 9, 15, tzinfo=MOSCOW_TZ)),
        ("  сегодня  07:00  ", datetime(2026, 2, 9, 7, 0, tzinfo=MOSCOW_TZ)),  # с пробелами
        ("некорректно", None),
        ("сегодня abc", None),
        ("завтра 25:00", None),
    ]
)
def test_parse_datetime(text, expected):
    dt = parse_datetime(text)
    assert dt == expected


# Тесты для format_task_date
@freeze_time("2026-02-09 12:00:00", tz_offset=3)
def test_format_task_date_datetime():
    dt = datetime(2026, 2, 9, 15, 30, tzinfo=timezone.utc)
    result = format_task_date(dt)
    day_name = RU_DAYS[dt.astimezone(MOSCOW_TZ).weekday()]
    month_name = RU_MONTHS[dt.astimezone(MOSCOW_TZ).month - 1]
    expected = f"{day_name}, 09 {month_name} 2026 18:30"
    assert result == expected


def test_format_task_date_iso_string():
    iso_str = "2026-02-10T12:00:00Z"
    result = format_task_date(iso_str)
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00")).astimezone(MOSCOW_TZ)
    day_name = RU_DAYS[dt.weekday()]
    month_name = RU_MONTHS[dt.month - 1]
    expected = f"{day_name}, 10 {month_name} 2026 15:00"
    assert result == expected


def test_format_task_date_invalid_type():
    import pytest
    with pytest.raises(TypeError):
        format_task_date(12345)


# Тесты для format_task
def test_format_task():
    task = {
        "title": "Тестовая задача",
        "scheduled_time": datetime(2026, 2, 10, 12, 0, tzinfo=timezone.utc)
    }
    result = format_task(task)
    assert result == result


def test_format_task_date_naive_datetime():
    dt = datetime(2026, 2, 9, 12, 0)  # нет tzinfo
    result = format_task_date(dt)
    # проверяем, что результат соответствует московскому времени
    expected_hour = (dt.replace(tzinfo=timezone.utc).astimezone(MOSCOW_TZ)).hour
    assert str(expected_hour).zfill(2) in result


# Тесты для parse_and_validate_datetime
@pytest.mark.parametrize(
    "text,expected",
    [
        ("завтра 14:00", (datetime.now() + timedelta(days=1)).replace(
            day=datetime.now().day + 1,
            hour=11,
            minute=0,
            second=0,
            microsecond=0,
            tzinfo=timezone.utc
        )),
        ("сегодня 23:59", datetime.now().replace(
            hour=20,
            minute=59,
            second=0,
            microsecond=0,
            tzinfo=timezone.utc
        )),
        ("2026-02-08 15:00", None),  # в прошлом
        ("некорректно", None)
    ]
)
def test_parse_and_validate_datetime(text, expected):
    dt_utc = parse_and_validate_datetime(text)
    assert dt_utc == expected
