import aiohttp

async def get_weather(city: str) -> dict:
    """
    Получаем погоду через wttr.in (без API ключа, работает на PythonAnywhere Free).
    Возвращает словарь с ключами 'description' и 'temp' или 'error'.
    """
    # wttr.in позволяет возвращать JSON
    url = f"http://wttr.in/{city}?format=j1"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return {"error": f"Ошибка получения погоды ({resp.status})"}
                data = await resp.json()
        except Exception as e:
            return {"error": f"Не удалось подключиться к API: {e}"}

    try:
        # Берём первый доступный прогноз
        current = data["current_condition"][0]
        description = current["weatherDesc"][0]["value"]
        temp = float(current["temp_C"])
        return {
            "weather": [{"description": description}],
            "main": {"temp": temp}
        }
    except Exception as e:
        return {"error": f"Ошибка обработки данных: {e}"}
