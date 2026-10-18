from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.keyboards import edit_keyboard, main_keyboard
from app.poll_service import (cancel_week, get_preview, prepare_week,
                              publish_poll, set_date, set_place, set_time, status)

router = Router()


class EditTraining(StatesGroup):
    waiting_date = State()
    waiting_time = State()
    waiting_place = State()


def is_admin(user_id):
    return user_id == settings.admin_id


async def menu(message: Message):
    prepare_week()
    s = status()
    suffix = {"draft": "", "published": "\n\n✅ Уже опубликовано.",
              "cancelled": "\n\n❌ Отменено.",
              "publishing": "\n\n⚠️ Публикация выполняется.",
              "uncertain": "\n\n⚠️ Проверь группу: результат публикации неизвестен."}[s]
    await message.answer(await get_preview() + suffix,
                         reply_markup=main_keyboard() if s == "draft" else None,
                         parse_mode="HTML")


@router.message(CommandStart())
async def start(message: Message):
    if is_admin(message.from_user.id if message.from_user else None):
        await message.answer("🏃 /poll — голосование; /status — состояние; /id — идентификаторы")
    else:
        await message.answer("🏃 Бот корпоративных тренировок.")


@router.message(Command("id"))
async def ids(message: Message):
    if not is_admin(message.from_user.id if message.from_user else None):
        return
    await message.answer(f"👤 User ID: {message.from_user.id}\n💬 Chat ID: {message.chat.id}\n🧵 Topic ID: {message.message_thread_id}")


@router.message(Command("poll", "status"))
async def poll_menu(message: Message):
    if is_admin(message.from_user.id if message.from_user else None):
        await menu(message)


@router.callback_query(F.data == "poll_weather")
async def refresh_weather(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    if status() != "draft":
        await callback.answer("Голосование уже завершено", show_alert=True)
        return
    await callback.answer("Обновляю прогноз…")
    preview = await get_preview()
    if "Прогноз на тренировку:" not in preview:
        await callback.message.answer("⚠️ Прогноз пока недоступен. Попробуйте позже.")
        return
    await callback.message.edit_text(
        "🗳 <b>Голосование на следующую тренировку</b>\n\n" +
        preview + "\n\nОпубликовать?",
        reply_markup=main_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "poll_publish")
async def publish(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    if status() != "draft":
        await callback.answer("Уже опубликовано, отменено или требует проверки", show_alert=True)
        return
    await callback.answer("Публикую…")
    try:
        result = await publish_poll(callback.bot)
    except Exception:
        await callback.message.answer("⚠️ Ошибка публикации. Проверь группу и логи, повтор автоматически заблокирован.")
        return
    if result:
        await callback.message.edit_text(await get_preview() + "\n\n✅ <b>Опубликовано.</b>", parse_mode="HTML")


@router.callback_query(F.data == "poll_edit")
async def edit(callback: CallbackQuery):
    if not is_admin(callback.from_user.id) or status() != "draft":
        await callback.answer("Редактирование недоступно", show_alert=True)
        return
    await callback.message.edit_text(await get_preview() + "\n\n<b>Что изменить?</b>",
                                     reply_markup=edit_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "edit_back")
async def back(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.message.edit_text(await get_preview(), reply_markup=main_keyboard() if status() == "draft" else None, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.in_({"edit_date", "edit_time", "edit_place"}))
async def begin_edit(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id) or status() != "draft":
        await callback.answer("Недоступно", show_alert=True)
        return
    mapping = {"edit_date": (EditTraining.waiting_date, "📅 Введите дату: ДД.ММ.ГГГГ"),
               "edit_time": (EditTraining.waiting_time, "🕐 Введите время: ЧЧ:ММ"),
               "edit_place": (EditTraining.waiting_place, "📍 Введите место:")}
    target, prompt = mapping[callback.data]
    await state.set_state(target)
    await callback.message.answer(prompt)
    await callback.answer()


@router.message(EditTraining.waiting_date)
@router.message(EditTraining.waiting_time)
@router.message(EditTraining.waiting_place)
async def receive_edit(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id if message.from_user else None):
        return
    current = await state.get_state()
    fn = {EditTraining.waiting_date.state: set_date,
          EditTraining.waiting_time.state: set_time,
          EditTraining.waiting_place.state: set_place}.get(current)
    try:
        fn((message.text or "").strip())
    except (ValueError, TypeError) as exc:
        await message.answer(f"❌ {exc}. Повторите ввод.")
        return
    await state.clear()
    await menu(message)


@router.callback_query(F.data == "poll_cancel")
async def cancel(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    try:
        cancel_week()
    except ValueError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    await callback.message.edit_text(await get_preview() + "\n\n❌ <b>Отменено.</b>", parse_mode="HTML")
    await callback.answer("Отменено")
