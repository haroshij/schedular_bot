from telegram.ext import ConversationHandler

# -------- Добавление задачи --------
ADD_DATE = 1
ADD_TEXT = 2

# -------- Отложить задачу --------
POSTPONE_DATE = 3

# -------- Погода --------
WEATHER_CITY = 4

# -------- Поиск --------
SEARCH_QUERY = 5

ALL_STATES = [
    ADD_DATE,
    ADD_TEXT,
    POSTPONE_DATE,
    WEATHER_CITY,
    SEARCH_QUERY,
]

END = ConversationHandler.END
