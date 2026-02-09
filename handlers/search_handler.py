from telegram import Update
from telegram.ext import CallbackContext
from services.search_service import search_duckduckgo
from handlers.common import cancel_menu_kb
from utils.search_utils import validate_search_query
from app.decorators import log_handler
from states import SEARCH_QUERY
from app.logger import logger


@log_handler
async def search_handler(update: Update, _: CallbackContext):
    query = update.message.text.strip()

    if not validate_search_query(query):
        await update.message.reply_text(
            "❌ Запрос некорректный. Попробуйте другой.",
            reply_markup=cancel_menu_kb()
        )
        logger.warning(
            'Пользователь %s ввёл некорректный запрос: %s',
            update.effective_user.id,
            query
        )
        return SEARCH_QUERY

    results = await search_duckduckgo(query)
    text = "\n\n".join(results[:5])
    await update.message.reply_text(
        text,
        reply_markup=cancel_menu_kb()  # добавляем кнопки для возврата в меню
    )

    return SEARCH_QUERY
