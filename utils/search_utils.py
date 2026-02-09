import re

SEARCH_RE = re.compile(r"^[\w\s\-.,!?]{2,200}$")  # простая валидация

def validate_search_query(query: str) -> bool:
    return bool(SEARCH_RE.match(query))
