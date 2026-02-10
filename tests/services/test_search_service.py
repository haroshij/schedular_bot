import asyncio

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from services.search_service import search_duckduckgo, main


@pytest.fixture
def mock_loop():
    loop = MagicMock()
    return loop


def make_future(result):
    fut = asyncio.Future()
    fut.set_result(result)
    return fut


@pytest.mark.asyncio
async def test_search_duckduckgo_success(mock_loop):
    fake_results = [
        {"title": "Python", "href": "https://python.org"},
        {"title": "Asyncio", "href": "https://docs.python.org/asyncio"},
    ]

    mock_loop.run_in_executor.return_value = make_future(fake_results)

    with patch("services.search_service.asyncio.get_running_loop", return_value=mock_loop), \
            patch("services.search_service.DDGS"):
        result = await search_duckduckgo("python")

    assert result == [
        "Python\nhttps://python.org",
        "Asyncio\nhttps://docs.python.org/asyncio",
    ]


@pytest.mark.asyncio
async def test_search_duckduckgo_empty_result(mock_loop):
    mock_loop.run_in_executor.return_value = make_future([])

    with patch("services.search_service.asyncio.get_running_loop", return_value=mock_loop), \
            patch("services.search_service.DDGS"):
        result = await search_duckduckgo("nothing")

    assert result == ["Ничего не найдено."]


@pytest.mark.asyncio
async def test_search_duckduckgo_skips_invalid_items(mock_loop):
    fake_results = [
        {"title": "Valid", "href": "https://example.com"},
        {"title": None, "href": "https://bad.com"},
        {"href": "https://bad.com"},
        {"title": "No link"},
    ]

    mock_loop.run_in_executor.return_value = make_future(fake_results)

    with patch("services.search_service.asyncio.get_running_loop", return_value=mock_loop), \
            patch("services.search_service.DDGS"):
        result = await search_duckduckgo("test")

    assert result == ["Valid\nhttps://example.com"]


@pytest.mark.asyncio
async def test_search_duckduckgo_exception(mock_loop):
    fut = asyncio.Future()
    fut.set_exception(RuntimeError("DDG down"))
    mock_loop.run_in_executor.return_value = fut

    with patch("services.search_service.asyncio.get_running_loop", return_value=mock_loop), \
            patch("services.search_service.DDGS"):
        result = await search_duckduckgo("error")

    assert result == ["Ошибка поиска: DDG down"]


@pytest.mark.asyncio
async def test_main_execution():
    fake_results = ["Result 1", "Result 2"]

    with patch("builtins.input", return_value="query"), \
         patch("services.search_service.search_duckduckgo", new=AsyncMock(return_value=fake_results)), \
         patch("builtins.print") as mock_print:
        await main()

    # Проверяем, что print вызван для каждого результата
    mock_print.assert_any_call("Result 1", "\n")
    mock_print.assert_any_call("Result 2", "\n")