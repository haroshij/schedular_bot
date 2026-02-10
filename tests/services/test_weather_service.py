import pytest
from unittest.mock import patch
from services import weather_service


# Мок для aiohttp ClientSession
class MockAiohttpResponse:
    def __init__(self, status=200, json_data=None):
        self.status = status
        self._json = json_data or {}

    async def json(self):
        return self._json

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class MockAiohttpSession:
    def __init__(self, response):
        self._response = response

    def get(self, _):
        return self._response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


# Тесты _get_weather
@pytest.mark.asyncio
async def test_get_weather_success():
    fake_data = {"current_condition": [{"weatherDesc": [{"value": "Sunny"}], "temp_C": "25"}]}
    mock_response = MockAiohttpResponse(status=200, json_data=fake_data)
    mock_session = MockAiohttpSession(response=mock_response)

    with patch("services.weather_service.aiohttp.ClientSession", return_value=mock_session):
        result = await weather_service._get_weather("Moscow")

    assert result == {
        "weather": [{"description": "Sunny"}],
        "main": {"temp": 25.0}
    }


@pytest.mark.asyncio
async def test_get_weather_http_error():
    mock_response = MockAiohttpResponse(status=404, json_data={})
    mock_session = MockAiohttpSession(response=mock_response)

    with patch("services.weather_service.aiohttp.ClientSession", return_value=mock_session):
        result = await weather_service._get_weather("Moscow")

    assert "error" in result
    assert "404" in result["error"]


@pytest.mark.asyncio
async def test_get_weather_json_error():
    class BadResponse(MockAiohttpResponse):
        async def json(self):
            raise ValueError("JSON parse error")

    mock_response = BadResponse(status=200)
    mock_session = MockAiohttpSession(response=mock_response)

    with patch("services.weather_service.aiohttp.ClientSession", return_value=mock_session):
        result = await weather_service._get_weather("Moscow")

    assert "error" in result
    assert "JSON" in result["error"] or "обработки данных" in result["error"]


# Тесты get_weather_with_translation
@pytest.mark.asyncio
async def test_get_weather_with_translation_success():
    fake_data = {
        "weather": [{"description": "Cloudy"}],
        "main": {"temp": 10.0}
    }

    with patch("services.weather_service.validate_city", return_value=True), \
            patch("services.weather_service._get_weather", return_value=fake_data), \
            patch("services.weather_service.translate_weather", side_effect=lambda x: f"RU-{x}"):
        result = await weather_service.get_weather_with_translation("Moscow")

    assert result == {
        "city": "Moscow",
        "description": "RU-Cloudy",
        "temp": 10.0
    }


@pytest.mark.asyncio
async def test_get_weather_with_translation_invalid_city():
    with patch("services.weather_service.validate_city", return_value=False):
        result = await weather_service.get_weather_with_translation("FakeCity")

    assert result == {"error": "Некорректное название города"}


@pytest.mark.asyncio
async def test_get_weather_with_translation_error_from_api():
    # Патчим _get_weather чтобы вернуть ошибку
    with patch("services.weather_service.validate_city", return_value=True), \
            patch("services.weather_service._get_weather", return_value={"error": "Ошибка получения погоды (500)"}):
        result = await weather_service.get_weather_with_translation("Moscow")

    assert "error" in result
    assert "500" in result["error"] or "Ошибка получения погоды" in result["error"]


@pytest.mark.asyncio
async def test_get_weather_data_processing_error():
    # Данные без current_condition вызовет KeyError
    fake_data = {"wrong_key": "oops"}
    mock_resp = MockAiohttpResponse(status=200, json_data=fake_data)
    mock_session = MockAiohttpSession(response=mock_resp)

    with patch("services.weather_service.aiohttp.ClientSession", return_value=mock_session):
        result = await weather_service._get_weather("Moscow")

    assert "error" in result
    assert "Ошибка обработки данных" in result["error"]
