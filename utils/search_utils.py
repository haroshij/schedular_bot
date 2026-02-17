import re

# Регулярное выражение для базовой валидации поискового запроса.
SEARCH_RE = re.compile(r"^[\w\s\-.,!?]{2,200}$")


def validate_search_query(query: str) -> bool:
    """
    Проверяет корректность поискового запроса пользователя.

    Args:
        query (str): Строка поискового запроса, введённая пользователем.

    Returns:
        bool: `True`, если запрос подходит под шаблон, иначе `False`.
    """

    return bool(SEARCH_RE.match(query))
