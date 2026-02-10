import sys
from pathlib import Path

import asyncio
from types import SimpleNamespace

import pytest

# Определяем корень проекта
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Добавляем PROJECT_ROOT в sys.path, если его там ещё нет
# Это нужно для корректного импорта модулей проекта в тестах
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# Фикстуры для pytest
@pytest.fixture(scope="session")
def event_loop():
    """
    Глобальный asyncio event loop для асинхронных тестов.
    Этот loop будет использоваться всеми тестами, которые требуют
    асинхронного выполнения, например, функции с async/await.

    Шаги:
    1. Создаем новый event loop
    2. Передаем его в тест через yield
    3. После завершения тестовой сессии loop закрывается
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def user_id():
    """
    Фикстура для предоставления идентификатора пользователя.
    """
    return 123456789


@pytest.fixture
def chat_id():
    """
    Фикстура для предоставления идентификатора чата.
    """
    return 987654321


@pytest.fixture
def fake_message():
    """
    Создает имитацию объекта сообщения от Telegram.
    Используется в тестах для проверки функций-обработчиков сообщений.
    Методы reply_text и edit_text заменены на простые лямбды,
    чтобы не выполнять реальные вызовы API.
    """
    return SimpleNamespace(
        text="test",
        reply_text=lambda *args, **kwargs: None,
        edit_text=lambda *args, **kwargs: None,
    )


@pytest.fixture
def fake_callback_query(fake_message):
    """
    Создает имитацию объекта CallbackQuery от Telegram.
    Используется в тестах для проверки обработки callback событий.
    """
    return SimpleNamespace(
        data="test_callback",
        message=fake_message,
        answer=lambda *args, **kwargs: None,
    )


@pytest.fixture
def fake_update(user_id, chat_id, fake_message, fake_callback_query):
    """
    Создает имитацию объекта Update от Telegram.
    Update содержит информацию о сообщении, callback, пользователе и чате.
    Используется для тестирования обработчиков команд и callback.
    """
    return SimpleNamespace(
        effective_user=SimpleNamespace(id=user_id),
        effective_chat=SimpleNamespace(id=chat_id),
        message=fake_message,
        callback_query=fake_callback_query,
    )


@pytest.fixture
def fake_context():
    """
    Создает и возвращает имитацию контекста для обработчиков Telegram.
    Контекст хранит пользовательские данные, данные бота и ссылку на приложение.
    Используется для передачи в функции-обработчики без необходимости реального приложения.
    """
    return SimpleNamespace(
        user_data={},
        bot_data={},
        application=None,
    )


@pytest.fixture(autouse=True)
def disable_logging(caplog):
    """
    Отключает вывод логов ниже уровня CRITICAL во время тестов.
    Это позволяет сделать вывод pytest чистым и удобным для чтения.
    """
    caplog.set_level("CRITICAL")
