import asyncio
from ddgs import DDGS


async def search_duckduckgo(query: str) -> list[str]:
    """
    Асинхронный поиск через duckduckgo_search.
    Оборачивает синхронный DDGS().text() в executor, чтобы не блокировать цикл.
    """
    ddgs = DDGS()
    loop = asyncio.get_running_loop()

    def search_ddgs():
        return ddgs.text(query, region="wt-wt", max_results=5)

    try:
        results = await loop.run_in_executor(None, search_ddgs)
    except Exception as e:
        results = [f"Ошибка поиска: {e}"]

    output = []
    if results:
        for item in results:
            # duckduckgo-search возвращает словари с ключами 'title' и 'href'
            title = item.get("title")
            link = item.get("href")
            if title and link:
                output.append(f"{title}\n{link}")
    else:
        output.append("Ничего не найдено.")

    return output


# Пример запуска
async def main():
    query = input("Введите запрос для поиска:")
    res = await search_duckduckgo(query)
    for r in res:
        print(r, "\n")


if __name__ == "__main__":
    asyncio.run(main())
