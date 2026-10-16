from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Опубликовать", callback_data="poll_publish")],
        [InlineKeyboardButton(text="✏️ Изменить", callback_data="poll_edit")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="poll_cancel")],
    ])


def edit_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Дата", callback_data="edit_date"),
         InlineKeyboardButton(text="🕐 Время", callback_data="edit_time")],
        [InlineKeyboardButton(text="📍 Место", callback_data="edit_place")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="edit_back")],
    ])
