import pytest
from unittest.mock import AsyncMock, MagicMock

from telegram import InlineKeyboardMarkup
from telegram.ext import ConversationHandler

from handlers.common.common import cancel_menu_kb, start, cancel
from keyboard import MAIN_MENU


# тест клавиатуры
def test_cancel_menu_kb():
    kb = cancel_menu_kb()

    assert isinstance(kb, InlineKeyboardMarkup)
    assert len(kb.inline_keyboard) == 2

    menu_btn = kb.inline_keyboard[0][0]
    cancel_btn = kb.inline_keyboard[1][0]

    assert menu_btn.text == "↩️ В меню"
    assert menu_btn.callback_data == "menu"

    assert cancel_btn.text == "❌ Отмена"
    assert cancel_btn.callback_data == "cancel"


# тест start
@pytest.mark.asyncio
async def test_start_handler():
    update = MagicMock()
    update.message.reply_text = AsyncMock()

    context = MagicMock()

    await start(update, context)

    update.message.reply_text.assert_awaited_once_with(
        "Привет! Выбери действие 👇",
        reply_markup=MAIN_MENU
    )


# тесты cancel
@pytest.mark.asyncio
async def test_cancel_with_callback_query():
    update = MagicMock()
    update.callback_query = MagicMock()
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()

    update.effective_user.id = 123

    context = MagicMock()
    context.user_data = {"temp": "data"}

    result = await cancel(update, context)

    update.callback_query.answer.assert_awaited_once()
    update.callback_query.edit_message_text.assert_awaited_once_with(
        "Действие отменено 👍\nВыбери действие 👇",
        reply_markup=MAIN_MENU
    )

    assert context.user_data == {}
    assert result == ConversationHandler.END


@pytest.mark.asyncio
async def test_cancel_with_message():
    update = MagicMock()
    update.callback_query = None
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()

    update.effective_user.id = 456

    context = MagicMock()
    context.user_data = {"temp": "data"}

    result = await cancel(update, context)

    update.message.reply_text.assert_awaited_once_with(
        "Действие отменено 👍\nВыбери действие 👇",
        reply_markup=MAIN_MENU
    )

    assert context.user_data == {}
    assert result == ConversationHandler.END
