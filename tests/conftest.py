import sys
from pathlib import Path

import asyncio
from types import SimpleNamespace

import pytest

# Корень проекта (schedular_bot/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def event_loop():
    """
    Глобальный event loop для async-тестов.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def user_id():
    return 123456789


@pytest.fixture
def chat_id():
    return 987654321


@pytest.fixture
def fake_message():
    return SimpleNamespace(
        text="test",
        reply_text=lambda *args, **kwargs: None,
        edit_text=lambda *args, **kwargs: None,
    )


@pytest.fixture
def fake_callback_query(fake_message):
    return SimpleNamespace(
        data="test_callback",
        message=fake_message,
        answer=lambda *args, **kwargs: None,
    )


@pytest.fixture
def fake_update(user_id, chat_id, fake_message, fake_callback_query):
    return SimpleNamespace(
        effective_user=SimpleNamespace(id=user_id),
        effective_chat=SimpleNamespace(id=chat_id),
        message=fake_message,
        callback_query=fake_callback_query,
    )


@pytest.fixture
def fake_context():
    return SimpleNamespace(
        user_data={},
        bot_data={},
        application=None,
    )


@pytest.fixture(autouse=True)
def disable_logging(caplog):
    """
    Отключаем логирование ниже CRITICAL,
    чтобы pytest вывод был чистым.
    """
    caplog.set_level("CRITICAL")
