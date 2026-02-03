import aiohttp

API_KEY = "ВАШ_GOOGLE_API_KEY"
CX = "ВАШ_SEARCH_ENGINE_ID"

async def search_google(query: str) -> list[str]:
    """
    Асинхронный поиск через Google Custom Search API.
    Возвращает список первых 5 ссылок.
    """
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": API_KEY,
        "cx": CX,
        "q": query,
        "num": 5
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                return [f"Ошибка поиска: {resp.status}"]

            data = await resp.json()
            items = data.get("items", [])
            results = []
            for item in items:
                title = item.get("title")
                link = item.get("link")
                results.append(f"{title}\n{link}")
            return results
