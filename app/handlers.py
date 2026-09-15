from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.keyboards import edit_keyboard, main_keyboard
from app.poll_service import (
    cancel_week,
    get_preview,
    prepare_week,
    publish_poll,
    set_date,
    set_place,
    set_time,
)


router = Router()


class EditTraining(StatesGroup):
    waiting_date = State()
    waiting_time = State()
    waiting_place = State()


def is_admin(
    user_id: int | None,
) -> bool:
    return user_id == settings.admin_id


async def send_admin_menu(
    message: Message,
) -> None:
    await message.answer(
        get_preview(),
        reply_markup=main_keyboard(),
        parse_mode="HTML",
    )


@router.message(CommandStart())
async def start_handler(
    message: Message,
) -> None:
    user_id = (
        message.from_user.id
        if message.from_user
        else None
    )

    if not is_admin(user_id):
        await message.answer(
            "🏃 Бот голосований по тренировкам."
        )
        return

    await message.answer(
        "🏃 <b>Тренировки</b>\n\n"
        "Управление еженедельными голосованиями.\n\n"
        "/poll — подготовить голосование",
        parse_mode="HTML",
    )


@router.message(Command("id"))
async def id_handler(
    message: Message,
) -> None:
    user_id = (
        message.from_user.id
        if message.from_user
        else None
    )

    if not is_admin(user_id):
        return

    await message.answer(
        f"👤 User ID: {user_id}\n"
        f"💬 Chat ID: {message.chat.id}\n"
        f"🧵 Topic ID: {message.message_thread_id}"
    )


@router.message(Command("poll"))
async def poll_handler(
    message: Message,
) -> None:
    user_id = (
        message.from_user.id
        if message.from_user
        else None
    )

    if not is_admin(user_id):
        return

    prepare_week()

    await send_admin_menu(message)


@router.message(Command("testpoll"))
async def test_poll_handler(
    message: Message,
) -> None:
    user_id = (
        message.from_user.id
        if message.from_user
        else None
    )

    if not is_admin(user_id):
        return

    prepare_week()

    published = await publish_poll(
        message.bot
    )

    if published:
        await message.answer(
            "✅ Тестовое голосование опубликовано."
        )
    else:
        await message.answer(
            "⚠️ Голосование не опубликовано."
        )


@router.callback_query(
    F.data == "poll_publish"
)
async def publish_callback(
    callback: CallbackQuery,
) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(
            "Нет доступа.",
            show_alert=True,
        )
        return

    published = await publish_poll(
        callback.bot
    )

    if not published:
        await callback.answer(
            "Голосование уже опубликовано "
            "или отменено.",
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        get_preview()
        + "\n\n"
        + "✅ <b>Голосование опубликовано.</b>",
        parse_mode="HTML",
    )

    await callback.answer(
        "Опубликовано."
    )


@router.callback_query(
    F.data == "poll_edit"
)
async def edit_callback(
    callback: CallbackQuery,
) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(
            "Нет доступа.",
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        get_preview()
        + "\n\n"
        + "<b>Что изменить?</b>",
        reply_markup=edit_keyboard(),
        parse_mode="HTML",
    )

    await callback.answer()


@router.callback_query(
    F.data == "edit_back"
)
async def edit_back_callback(
    callback: CallbackQuery,
) -> None:
    if not is_admin(callback.from_user.id):
        return

    await callback.message.edit_text(
        get_preview(),
        reply_markup=main_keyboard(),
        parse_mode="HTML",
    )

    await callback.answer()


@router.callback_query(
    F.data == "edit_date"
)
async def edit_date_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(
        EditTraining.waiting_date
    )

    await callback.message.answer(
        "📅 Введите дату тренировки.\n\n"
        "Формат: <code>21.09.2026</code>",
        parse_mode="HTML",
    )

    await callback.answer()


@router.callback_query(
    F.data == "edit_time"
)
async def edit_time_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(
        EditTraining.waiting_time
    )

    await callback.message.answer(
        "🕐 Введите время тренировки.\n\n"
        "Формат: <code>19:30</code>",
        parse_mode="HTML",
    )

    await callback.answer()


@router.callback_query(
    F.data == "edit_place"
)
async def edit_place_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(
        EditTraining.waiting_place
    )

    await callback.message.answer(
        "📍 Введите место тренировки:"
    )

    await callback.answer()


@router.message(
    EditTraining.waiting_date
)
async def receive_date(
    message: Message,
    state: FSMContext,
) -> None:
    user_id = (
        message.from_user.id
        if message.from_user
        else None
    )

    if not is_admin(user_id):
        return

    value = (
        message.text or ""
    ).strip()

    try:
        datetime.strptime(
            value,
            "%d.%m.%Y",
        )

    except ValueError:
        await message.answer(
            "❌ Неверный формат даты.\n\n"
            "Например: "
            "<code>21.09.2026</code>",
            parse_mode="HTML",
        )
        return

    set_date(value)

    await state.clear()

    await message.answer(
        "✅ Дата изменена.\n\n"
        + get_preview(),
        reply_markup=main_keyboard(),
        parse_mode="HTML",
    )


@router.message(
    EditTraining.waiting_time
)
async def receive_time(
    message: Message,
    state: FSMContext,
) -> None:
    user_id = (
        message.from_user.id
        if message.from_user
        else None
    )

    if not is_admin(user_id):
        return

    value = (
        message.text or ""
    ).strip()

    try:
        datetime.strptime(
            value,
            "%H:%M",
        )

    except ValueError:
        await message.answer(
            "❌ Неверный формат времени.\n\n"
            "Например: "
            "<code>19:30</code>",
            parse_mode="HTML",
        )
        return

    set_time(value)

    await state.clear()

    await message.answer(
        "✅ Время изменено.\n\n"
        + get_preview(),
        reply_markup=main_keyboard(),
        parse_mode="HTML",
    )


@router.message(
    EditTraining.waiting_place
)
async def receive_place(
    message: Message,
    state: FSMContext,
) -> None:
    user_id = (
        message.from_user.id
        if message.from_user
        else None
    )

    if not is_admin(user_id):
        return

    value = (
        message.text or ""
    ).strip()

    if not value:
        await message.answer(
            "❌ Место не может быть пустым."
        )
        return

    set_place(value)

    await state.clear()

    await message.answer(
        "✅ Место изменено.\n\n"
        + get_preview(),
        reply_markup=main_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(
    F.data == "poll_cancel"
)
async def cancel_callback(
    callback: CallbackQuery,
) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(
            "Нет доступа.",
            show_alert=True,
        )
        return

    cancel_week()

    await callback.message.edit_text(
        get_preview()
        + "\n\n"
        + "❌ <b>Голосование на эту неделю "
        + "отменено.</b>",
        parse_mode="HTML",
    )

    await callback.answer(
        "Голосование отменено."
    )
