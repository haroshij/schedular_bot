from telegram import Update
from telegram.ext import CallbackContext

from handlers.search import search_duckduckgo


async def search_handler(update: Update, _: CallbackContext):
    query = update.message.text.strip()
    results = await search_duckduckgo(query)
    text = "\n\n".join(results[:5])
    await update.message.reply_text(text)
