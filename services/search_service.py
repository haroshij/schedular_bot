import asyncio
from ddgs import DDGS
from app.logger import logger


async def search_duckduckgo(query: str) -> list[str]:
    """
    Выполняет асинхронный поиск в DuckDuckGo по заданному запросу.
    Поиск оборачивается в `run_in_executor`, чтобы не блокировать
    основной event loop asyncio.

    Args:
        query (str): Поисковый запрос, введённый пользователем.

    Returns:
        list[str]: Список строк с результатами поиска.
        Каждый элемент содержит заголовок и ссылку,
        либо сообщение об ошибке / отсутствии результатов.
    """

    ddgs = DDGS()  # Создаём экземпляр клиента DuckDuckGo Search
    loop = asyncio.get_running_loop()  # Получаем текущий асинхронный event loop
    logger.info("Запуск поиска через DDGS (Dux Distributed Global Search)...")

    def search_ddgs():  # pragma: no cover
        """
        Синхронная функция-обёртка для вызова DDGS().text().
        Выделена в отдельную функцию, чтобы передать её
        в executor и выполнить в другом потоке.
        pragma: no cover — исключает функцию из покрытия тестами,
        так как она используется только как внутренняя обёртка.
        """
        return ddgs.text(query, region="wt-wt", max_results=5)

    try:
        # Выполняем синхронный поиск в пуле потоков,
        # чтобы не блокировать asyncio event loop
        results = await asyncio.wait_for(
            loop.run_in_executor(None, search_ddgs),  # type: ignore
            timeout=10,  # таймаут в секундах
        )
    except Exception as e:
        # Логируем ошибку поиска
        logger.warning(
            "Ошибка поиска через DDGS (Dux Distributed Global Search)\n%s", e
        )
        return ["Произошла ошибка при поиске. Попробуйте позже."]

    output = []

    if results:
        for item in results:
            title = item.get("title")  # duckduckgo-search возвращает словари,
            link = item.get("href")  # содержащие ключи 'title' и 'href'

            if title and link:
                output.append(f"{title}\n{link}")
    else:
        output.append("Ничего не найдено.")

    logger.info("Поиска через DDGS (Dux Distributed Global Search) завершён")

    return output


async def main():
    """
    Точка входа для локального тестирования модуля поиска.
    """

    query = input("Введите запрос для поиска:")
    res = await search_duckduckgo(query)
    for r in res:
        print(r, "\n")


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(main())
