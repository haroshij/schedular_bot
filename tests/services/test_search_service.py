"""
Тестовый модуль для services.search_service.
"""

import asyncio
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from services.search_service import search_duckduckgo, main


@pytest.fixture
def mock_loop():
    """
    Фикстура, возвращающая mock event loop для подмены asyncio.get_running_loop
    и контроля поведения run_in_executor без запуска реального event loop.
    """

    loop = MagicMock()
    return loop


def make_future(result):
    """
    Создаёт asyncio.Future с заранее установленным результатом.
    Используется для имитации асинхронного выполнения функции
    внутри run_in_executor.
    """
    fut = asyncio.Future()
    fut.set_result(result)
    return fut


@pytest.mark.asyncio
async def test_search_duckduckgo_success(mock_loop):
    """
    Проверяет успешный сценарий поиска.
    """

    fake_results = [
        {"title": "Python", "href": "https://python.org"},
        {"title": "Asyncio", "href": "https://docs.python.org/asyncio"},
    ]

    # run_in_executor возвращает future с результатами
    mock_loop.run_in_executor.return_value = make_future(fake_results)

    # Подменяем event loop и класс DDGS
    with (
        patch(
            "services.search_service.asyncio.get_running_loop", return_value=mock_loop
        ),
        patch("services.search_service.DDGS"),
    ):
        result = await search_duckduckgo("python")

    # Проверяем корректность форматирования результатов
    assert result == [
        "Python\nhttps://python.org",
        "Asyncio\nhttps://docs.python.org/asyncio",
    ]


@pytest.mark.asyncio
async def test_search_duckduckgo_empty_result(mock_loop):
    """
    Проверяет поведение при пустой выдаче поиска.
    """
    # run_in_executor возвращает future с пустым списком
    mock_loop.run_in_executor.return_value = make_future([])

    # Подменяем event loop и DDGS
    with (
        patch(
            "services.search_service.asyncio.get_running_loop", return_value=mock_loop
        ),
        patch("services.search_service.DDGS"),
    ):
        result = await search_duckduckgo("nothing")

    # Проверяем сообщение по умолчанию
    assert result == ["Ничего не найдено."]


@pytest.mark.asyncio
async def test_search_duckduckgo_skips_invalid_items(mock_loop):
    """
    Проверяет, что некорректные элементы выдачи игнорируются.
    """
    # Фейковая выдача с валидными и невалидными элементами
    fake_results = [
        {"title": "Valid", "href": "https://example.com"},
        {"title": "Valid", "href": None},
        {"title": None, "href": "https://bad.com"},
        {"title": None, "href": None},
        {"href": "https://bad.com"},
        {"title": "No link"},
    ]

    # run_in_executor возвращает future с фейковыми данными
    mock_loop.run_in_executor.return_value = make_future(fake_results)

    # Подменяем event loop и DDGS
    with (
        patch(
            "services.search_service.asyncio.get_running_loop", return_value=mock_loop
        ),
        patch("services.search_service.DDGS"),
    ):
        result = await search_duckduckgo("test")

    assert result == ["Valid\nhttps://example.com"]


@pytest.mark.asyncio
async def test_search_duckduckgo_exception(mock_loop):
    """
    Проверяет обработку исключения во время поиска.
    """
    # Создаём future с исключением
    fut = asyncio.Future()
    fut.set_exception(RuntimeError("DDG down"))
    mock_loop.run_in_executor.return_value = fut

    # Подменяем event loop и DDGS
    with (
        patch(
            "services.search_service.asyncio.get_running_loop", return_value=mock_loop
        ),
        patch("services.search_service.DDGS"),
    ):
        result = await search_duckduckgo("error")

    # Проверяем корректное сообщение об ошибке
    assert result == ["Произошла ошибка при поиске. Попробуйте позже."]


@pytest.mark.asyncio
async def test_main_execution():
    """
    Проверяет работу функции main при запуске модуля.
    """
    fake_results = ["Result 1", "Result 2"]

    # Подменяем input, search_duckduckgo и print
    with (
        patch("builtins.input", return_value="query"),
        patch(
            "services.search_service.search_duckduckgo",
            new=AsyncMock(return_value=fake_results),
        ),
        patch("builtins.print") as mock_print,
    ):
        await main()

    # Проверяем, что print был вызван для каждого результата
    mock_print.assert_any_call("Result 1", "\n")
    mock_print.assert_any_call("Result 2", "\n")
