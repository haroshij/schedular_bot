from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
from services.search_service import search_duckduckgo
from handlers.common import cancel_menu_kb
from utils.search_utils import validate_search_query

async def search_handler(update: Update, _: CallbackContext):
    query = update.message.text.strip()

    if not validate_search_query(query):
        await update.message.reply_text(
            "❌ Запрос некорректный. Попробуйте другой.",
            reply_markup=cancel_menu_kb()
        )
        return ConversationHandler.END

    results = await search_duckduckgo(query)
    text = "\n\n".join(results[:5])
    await update.message.reply_text(
        text,
        reply_markup=cancel_menu_kb()  # добавляем кнопки для возврата в меню
    )

    return ConversationHandler.END