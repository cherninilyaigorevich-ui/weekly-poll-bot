"""Poll domain logic. A publishing state prevents duplicates after restart.

If Telegram accepts the poll but the response is lost, status becomes uncertain;
manual verification is required rather than risking a second poll.
"""
import asyncio
import logging
from datetime import date
from html import escape

from aiogram import Bot

from app.config import settings
from app.state import store
from app.weather import get_weather

logger = logging.getLogger(__name__)
_lock = asyncio.Lock()
MONTHS = ("", "января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря")
DAYS = ("понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье")


def format_date(value: date) -> str:
    return f"{value.day} {MONTHS[value.month]} {value.year} ({DAYS[value.weekday()]})"


def status() -> str:
    return store.get_or_create().status


def prepare_week():
    return store.get_or_create()


def set_date(value: str):
    from datetime import datetime
    obj = store.get_or_create()
    if obj.status != "draft":
        raise ValueError("Голосование уже опубликовано, отменено или требует проверки")
    obj.date = datetime.strptime(value, "%d.%m.%Y").date().isoformat()
    store.save()


def set_time(value: str):
    from datetime import datetime
    obj = store.get_or_create()
    if obj.status != "draft":
        raise ValueError("Нельзя изменить завершённое голосование")
    datetime.strptime(value, "%H:%M")
    obj.time = value
    store.save()


def set_place(value: str):
    obj = store.get_or_create()
    if obj.status != "draft":
        raise ValueError("Нельзя изменить завершённое голосование")
    if not value.strip():
        raise ValueError("Место не может быть пустым")
    obj.place = value.strip()
    store.save()


def cancel_week():
    if status() != "draft":
        raise ValueError("Нельзя отменить опубликованное голосование")
    store.set_status("cancelled")


async def get_preview() -> str:
    obj = store.get_or_create()
    base = (f"🏃 <b>Тренировка</b>\n"
            f"📅 <b>Дата:</b> {format_date(date.fromisoformat(obj.date))}\n"
            f"🕐 <b>Время:</b> {escape(obj.time)}\n"
            f"📍 <b>Место:</b> {escape(obj.place)}\n"
            "🏢 <b>Формат:</b> Корпоративная")
    forecast = await get_weather(date.fromisoformat(obj.date), obj.time)
    if forecast:
        base += "\n\n" + forecast
    return base + "\n\nУкажи свой ответ 👇"


async def publish_poll(bot: Bot) -> bool:
    async with _lock:
        obj = store.get_or_create()
        if obj.status != "draft":
            return False
        # Persist before network I/O: at-most-once attempt, with manual recovery.
        store.set_status("publishing")
        try:
            text = await get_preview()
            message = await bot.send_message(
                chat_id=settings.group_id, message_thread_id=settings.topic_id,
                text=text, parse_mode="HTML")
            obj.message_id = message.message_id
            store.save()
            poll = await bot.send_poll(
                chat_id=settings.group_id, message_thread_id=settings.topic_id,
                question="Ты будешь на тренировке?",
                options=["✅ Иду.", "❌ Не иду.", "❓ Под вопросом."],
                is_anonymous=False, allows_multiple_answers=False)
            obj.poll_id = poll.poll.id
            store.set_status("published")
            return True
        except Exception:
            logger.exception("Publication uncertain; inspect Telegram before manual recovery")
            store.set_status("uncertain")
            raise
