import pytest
from unittest.mock import patch
from services import weather_service


# Моки для aiohttp ClientSession и Response
class MockAiohttpResponse:
    """
    Мок объекта ответа aiohttp.

    Этот класс используется для имитации реального ответа от API погоды.
    Поддерживает асинхронный контекстный менеджер (async with) и метод json(),
    который возвращает заранее определенные данные.
    """

    def __init__(self, status=200, json_data=None):
        """
        Инициализация мок-объекта.

        Args:
            status (int): HTTP-статус ответа (по умолчанию 200 — успешный запрос)
            json_data (dict): Данные, которые должен вернуть метод json()
        """
        self.status = status
        self._json = json_data or {}  # Если json_data не передан, возвращаем пустой словарь

    async def json(self):
        """
        Возвращает заранее заданные данные JSON.

        Имитирует асинхронный метод response.json() из aiohttp.
        """
        return self._json

    async def __aenter__(self):
        """
        Поддержка конструкции async with.
        Возвращает сам объект при входе в контекст.
        """
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """
        Поддержка конструкции async with.
        Ничего не делает при выходе из контекста.
        """
        return False


class MockAiohttpSession:
    """
    Мок объекта aiohttp.ClientSession.

    При вызове session.get() возвращает заранее заданный мокированный response.
    Также поддерживает async with.
    """

    def __init__(self, response):
        """
        Инициализация мок-сессии.

        Args:
            response (MockAiohttpResponse): Объект ответа, который будет возвращаться при вызове get()
        """
        self._response = response  # Сохраняем объект ответа

    def get(self, _):
        """
        Имитирует метод session.get(url).

        Args:
            _ (str): URL (не используется, так как возвращаем заранее заданный response)

        Returns:
            MockAiohttpResponse: мокированный объект ответа
        """
        return self._response

    async def __aenter__(self):
        """
        Поддержка async with.
        Возвращает сам объект сессии.
        """
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """
        Поддержка async with.
        Ничего не делает при выходе из контекста.
        """
        return False


# Тесты функции _get_weather
@pytest.mark.asyncio
async def test_get_weather_success():
    """
    Проверка успешного получения данных погоды через _get_weather.

    Функция должна корректно обрабатывать JSON с ключами
    'current_condition', 'weatherDesc' и 'temp_C', и возвращать
    словарь с ключами 'weather' и 'main'.
    """
    # Задаем фейковые данные API
    fake_data = {
        "current_condition": [
            {"weatherDesc": [{"value": "Sunny"}], "temp_C": "25"}
        ]
    }

    # Создаем мок-объект ответа с фейковыми данными и статусом 200
    mock_response = MockAiohttpResponse(status=200, json_data=fake_data)

    # Создаем мок-сессию aiohttp.ClientSession, которая возвращает mock_response
    mock_session = MockAiohttpSession(response=mock_response)

    # Патчим ClientSession, чтобы функция _get_weather использовала наш мок
    with patch("services.weather_service.aiohttp.ClientSession", return_value=mock_session):
        result = await weather_service._get_weather("Moscow")

    # Проверяем, что результат преобразован правильно
    assert result == {
        "weather": [{"description": "Sunny"}],
        "main": {"temp": 25.0}
    }


@pytest.mark.asyncio
async def test_get_weather_http_error():
    """
    Проверка обработки HTTP ошибки (например, 404) при запросе погоды.

    Функция должна вернуть словарь с ключом 'error' и указанием кода ошибки.
    """
    # Создаем мок-ответ с кодом 404
    mock_response = MockAiohttpResponse(status=404, json_data={})

    # Создаем мок-сессию, возвращающую mock_response
    mock_session = MockAiohttpSession(response=mock_response)

    # Патчим ClientSession на мок
    with patch("services.weather_service.aiohttp.ClientSession", return_value=mock_session):
        result = await weather_service._get_weather("Moscow")

    # Проверяем наличие ключа 'error' и кода 404 в сообщении
    assert "error" in result
    assert "404" in result["error"]


@pytest.mark.asyncio
async def test_get_weather_json_error():
    """
    Проверка обработки ошибки при парсинге JSON.

    Если метод response.json() выбрасывает исключение, функция должна
    вернуть словарь с ключом 'error'.
    """

    class BadResponse(MockAiohttpResponse):
        async def json(self):
            # Имитируем ошибку при обработке JSON
            raise ValueError("JSON parse error")

    # Создаём мок с неправильным JSON
    mock_response = BadResponse(status=200)
    mock_session = MockAiohttpSession(response=mock_response)

    # Патчим ClientSession
    with patch("services.weather_service.aiohttp.ClientSession", return_value=mock_session):
        result = await weather_service._get_weather("Moscow")

    # Проверяем наличие ключа 'error' и текста ошибки
    assert "error" in result
    assert "JSON" in result["error"] or "обработки данных" in result["error"]


# Тесты функции get_weather_with_translation
@pytest.mark.asyncio
async def test_get_weather_with_translation_success():
    """
    Проверка успешного получения погоды с переводом описания на русский.

    Функция должна валидировать город, получить данные через _get_weather,
    перевести описание через translate_weather и вернуть словарь с ключами
    'city', 'description' и 'temp'.
    """
    fake_data = {
        "weather": [{"description": "Cloudy"}],
        "main": {"temp": 10.0}
    }

    # Патчим функции validate_city, _get_weather и translate_weather
    with patch("services.weather_service.validate_city", return_value=True), \
            patch("services.weather_service._get_weather", return_value=fake_data), \
            patch("services.weather_service.translate_weather", side_effect=lambda x: f"RU-{x}"):
        result = await weather_service.get_weather_with_translation("Moscow")

    # Проверяем корректность результата
    assert result == {
        "city": "Moscow",
        "description": "RU-Cloudy",
        "temp": 10.0
    }


@pytest.mark.asyncio
async def test_get_weather_with_translation_invalid_city():
    """
    Проверка поведения функции get_weather_with_translation при некорректном названии города.

    Функция должна сначала вызвать validate_city для проверки названия города.
    Если город невалиден, функция возвращает словарь с ключом 'error'
    и не вызывает внутренние функции _get_weather и translate_weather.
    """
    # Патчим validate_city, чтобы она вернула False (город невалидный)
    # Это имитирует случай, когда пользователь ввёл неправильное название города
    with patch("services.weather_service.validate_city", return_value=False):
        # Вызываем функцию с некорректным городом
        result = await weather_service.get_weather_with_translation("FakeCity")

    # Проверяем, что функция вернула словарь с ключом 'error' и корректным сообщением
    # Здесь мы проверяем именно логику "раннего выхода" при некорректном городе
    assert result == {"error": "Некорректное название города"}


@pytest.mark.asyncio
async def test_get_weather_with_translation_error_from_api():
    """
    Проверка обработки ошибки, возвращаемой _get_weather.

    Если _get_weather возвращает словарь с ключом 'error',
    get_weather_with_translation должна вернуть этот же словарь.
    Это позволяет правильно обрабатывать ошибки от внешнего API,
    не вызывая translate_weather.
    """
    # Патчим validate_city, чтобы город считался валидным
    # Патчим _get_weather, чтобы она вернула заранее определённую ошибку
    # Это имитация ситуации, когда API погоды вернул ошибку
    with patch("services.weather_service.validate_city", return_value=True), \
            patch("services.weather_service._get_weather", return_value={"error": "Ошибка получения погоды (500)"}):
        # Вызываем функцию с валидным городом, но _get_weather вернёт ошибку
        result = await weather_service.get_weather_with_translation("Moscow")

    # Проверяем, что функция корректно вернула словарь с ключом 'error'
    # и текстом ошибки, включая код 500 или сообщение от API
    assert "error" in result
    assert "500" in result["error"] or "Ошибка получения погоды" in result["error"]


@pytest.mark.asyncio
async def test_get_weather_data_processing_error():
    """
    Проверка обработки некорректной структуры данных от API.

    Например, отсутствует ключ 'current_condition'. Функция должна
    вернуть словарь с ключом 'error'.
    """
    # Создаем фейковые данные с неправильной структурой
    fake_data = {"wrong_key": "oops"}

    # Создаем мок-ответ и мок-сессию для этих данных
    mock_resp = MockAiohttpResponse(status=200, json_data=fake_data)
    mock_session = MockAiohttpSession(response=mock_resp)

    # Патчим ClientSession на мок
    with patch("services.weather_service.aiohttp.ClientSession", return_value=mock_session):
        result = await weather_service._get_weather("Moscow")

    # Проверяем, что функция вернула словарь с ключом 'error'
    assert "error" in result
    assert "Ошибка обработки данных" in result["error"]
