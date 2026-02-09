import re

CITY_RE = re.compile(r"^[A-Za-zА-Яа-яЁё \-]{2,50}$")

def validate_city(city: str) -> bool:
    return bool(CITY_RE.match(city))
