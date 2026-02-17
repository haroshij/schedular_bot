"""Состояния бота для ConversationHandler"""

from telegram.ext import ConversationHandler

ADD_DATE = 1
ADD_TEXT = 2
POSTPONE_DATE = 3
WEATHER_CITY = 4
SEARCH_QUERY = 5

END = ConversationHandler.END
