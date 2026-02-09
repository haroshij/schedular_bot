import pytest

from utils.search_utils import validate_search_query


@pytest.mark.parametrize(
    "query",
    [
        "hi",
        "hello world",
        "python-telegram bot",
        "что такое async",
        "test, with punctuation!",
        "numbers 123",
        "dots.and,commas",
        "A" * 200,  # граничное значение по длине
    ],
)
def test_validate_search_query_valid(query):
    assert validate_search_query(query) is True


@pytest.mark.parametrize(
    "query",
    [
        "",                 # пустая строка
        "a",                # слишком короткая
        " ",                # один пробел
        "\n",               # перевод строки
        "🔥",               # emoji
        "<script>",         # HTML
        "SELECT * FROM",    # SQL-подобное
        "A" * 201,          # слишком длинная
    ],
)
def test_validate_search_query_invalid(query):
    assert validate_search_query(query) is False


def test_validate_search_query_none_raises():
    """
    Явно фиксируем поведение:
    функция не принимает None.
    """
    with pytest.raises(TypeError):
        validate_search_query(None)  # type: ignore
