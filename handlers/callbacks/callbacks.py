from telegram import Update
from telegram.ext import CallbackContext

from handlers.callbacks.callbacks_menu import handle_menu_callbacks
from handlers.callbacks.callbacks_tasks import handle_tasks_callbacks
from handlers.callbacks.callbacks_weather import handle_weather_callbacks
from handlers.callbacks.callbacks_search import handle_search_callbacks
from app.decorators import log_handler


@log_handler
async def callbacks(update: Update, context: CallbackContext):
    query = update.callback_query
    if not query:
        return None

    await query.answer()
    data = query.data

    for handler in (
            handle_menu_callbacks,
            handle_tasks_callbacks,
            handle_weather_callbacks,
            handle_search_callbacks,
    ):
        result = await handler(update, context, data)
        if result is not None:
            return result

    return None
