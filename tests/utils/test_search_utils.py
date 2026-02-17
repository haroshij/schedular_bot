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
        "A" * 200,  # граничное значение по длине (максимально допустимое)
    ],
)
def test_validate_search_query_valid(query):
    """
    Проверка функции validate_search_query для корректных поисковых запросов.
    """
    assert validate_search_query(query) is True


@pytest.mark.parametrize(
    "query",
    [
        "",  # пустая строка
        "a",  # слишком короткая (меньше 2 символов)
        " ",  # только пробел
        "\n",  # только перевод строки
        "🔥",  # emoji (невалидный символ)
        "<script>",  # HTML-теги (невалидные символы)
        "SELECT * FROM",  # SQL-подобный ввод (невалидный)
        "A" * 201,  # слишком длинная строка (>200 символов)
    ],
)
def test_validate_search_query_invalid(query):
    """
    Проверка функции validate_search_query для некорректных поисковых запросов.
    """
    assert validate_search_query(query) is False


def test_validate_search_query_none_raises():
    """
    Проверка поведения функции validate_search_query при передаче None.
    Функция должна выбрасывать TypeError, так как None не является допустимым типом строки.
    """
    with pytest.raises(TypeError):
        validate_search_query(None)  # type: ignore
