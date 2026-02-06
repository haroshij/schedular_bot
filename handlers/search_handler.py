from telegram import Update
from telegram.ext import CallbackContext
from services.search_service import search_duckduckgo
from handlers.common import cancel_menu_kb


async def search_handler(update: Update, _: CallbackContext):
    query = update.message.text.strip()
    results = await search_duckduckgo(query)
    text = "\n\n".join(results[:5])
    await update.message.reply_text(
        text,
        reply_markup=cancel_menu_kb()  # добавляем кнопки для возврата в меню
    )
