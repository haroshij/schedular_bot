"""
Тестовый модуль для handlers.common.common.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from telegram import InlineKeyboardMarkup
from telegram.ext import ConversationHandler

from handlers.common.common import cancel_menu_kb, start, cancel
from keyboard import MAIN_MENU


def test_cancel_menu_kb():
    """
    Проверяет корректность клавиатуры отмены и возврата в меню.
    """

    kb = cancel_menu_kb()
    assert isinstance(kb, InlineKeyboardMarkup)
    assert len(kb.inline_keyboard) == 1

    cancel_btn = kb.inline_keyboard[0][0]
    assert cancel_btn.text == "❌ Отмена"
    assert cancel_btn.callback_data == "cancel"


@pytest.mark.asyncio
async def test_start_handler():
    """
    Проверяет работу стартового хендлера (/start).
    """

    update = MagicMock()  # Создаём mock-объект update с асинхронным reply_text
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    await start(update, context)

    # Проверяем, что сообщение отправлено с правильным текстом и клавиатурой
    update.message.reply_text.assert_awaited_once_with(
        "Привет! Выбери действие 👇", reply_markup=MAIN_MENU
    )


@pytest.mark.asyncio
async def test_cancel_with_callback_query():
    """
    Проверяет работу хендлера cancel при callback-запросе.
    """

    update = MagicMock()  # Создаём mock update с callback_query
    update.callback_query = MagicMock()
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.effective_user.id = 123
    context = MagicMock()  # Создаём контекст с временными данными
    context.user_data = {"temp": "data"}

    result = await cancel(update, context)  # Вызываем хендлер отмены

    # Проверяем, что callback_query был подтверждён
    update.callback_query.answer.assert_awaited_once()

    # Проверяем, что сообщение было отредактировано с нужным текстом и клавиатурой
    update.callback_query.edit_message_text.assert_awaited_once_with(
        "Действие отменено 👍\nВыбери действие 👇", reply_markup=MAIN_MENU
    )

    # Проверяем, что временные данные пользователя очищены
    assert context.user_data == {}

    # Проверяем, что диалог корректно завершён
    assert result == ConversationHandler.END


@pytest.mark.asyncio
async def test_cancel_with_message():
    """
    Проверяет работу хендлера cancel при обычном текстовом сообщении.
    """
    # Создаём mock update без callback_query, но с message
    update = MagicMock()
    update.callback_query = None
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    update.effective_user.id = 456

    context = MagicMock()  # Создаём контекст с временными данными
    context.user_data = {"temp": "data"}

    result = await cancel(update, context)  # Вызываем хендлер отмены

    # Проверяем, что сообщение отправлено с нужным текстом и клавиатурой
    update.message.reply_text.assert_awaited_once_with(
        "Действие отменено 👍\nВыбери действие 👇", reply_markup=MAIN_MENU
    )

    # Проверяем, что временные данные пользователя очищены
    assert context.user_data == {}

    # Проверяем, что диалог корректно завершён
    assert result == ConversationHandler.END
