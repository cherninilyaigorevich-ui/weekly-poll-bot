from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot

from app.config import settings


MONTHS_RU = {
    1: "января",
    2: "февраля",
    3: "марта",
    4: "апреля",
    5: "мая",
    6: "июня",
    7: "июля",
    8: "августа",
    9: "сентября",
    10: "октября",
    11: "ноября",
    12: "декабря",
}

WEEKDAYS_RU = {
    0: "понедельник",
    1: "вторник",
    2: "среда",
    3: "четверг",
    4: "пятница",
    5: "суббота",
    6: "воскресенье",
}


@dataclass
class TrainingPoll:
    date: datetime
    time: str
    place: str


current_training: TrainingPoll | None = None

poll_published = False
poll_cancelled = False
poll_prepared = False


def get_next_monday() -> datetime:
    now = datetime.now(
        ZoneInfo(settings.timezone)
    )

    days_until_monday = (7 - now.weekday()) % 7

    if days_until_monday == 0:
        days_until_monday = 7

    return now + timedelta(
        days=days_until_monday
    )


def create_default_training() -> TrainingPoll:
    return TrainingPoll(
        date=get_next_monday(),
        time=settings.default_time,
        place=settings.default_place,
    )


def prepare_week() -> TrainingPoll:
    global current_training
    global poll_published
    global poll_cancelled
    global poll_prepared

    current_training = create_default_training()

    poll_published = False
    poll_cancelled = False
    poll_prepared = True

    return current_training


def get_training() -> TrainingPoll:
    global current_training

    if current_training is None:
        current_training = create_default_training()

    return current_training


def format_training_date(
    value: datetime,
) -> str:
    return (
        f"{value.day} "
        f"{MONTHS_RU[value.month]} "
        f"{value.year} "
        f"({WEEKDAYS_RU[value.weekday()]})"
    )


def set_date(value: str) -> None:
    training = get_training()

    parsed_date = datetime.strptime(
        value,
        "%d.%m.%Y",
    )

    training.date = parsed_date.replace(
        tzinfo=ZoneInfo(settings.timezone)
    )


def set_time(value: str) -> None:
    get_training().time = value


def set_place(value: str) -> None:
    get_training().place = value


def cancel_week() -> None:
    global poll_cancelled

    poll_cancelled = True


def is_cancelled() -> bool:
    return poll_cancelled


def is_published() -> bool:
    return poll_published


def is_prepared() -> bool:
    return poll_prepared


def is_pending() -> bool:
    return (
        poll_prepared
        and not poll_published
        and not poll_cancelled
    )


def get_preview() -> str:
    training = get_training()

    date_text = format_training_date(
        training.date
    )

    return (
        "🏃 <b>Тренировка</b>\n"
        f"📅 <b>Дата:</b> {date_text}\n"
        f"🕐 <b>Время:</b> {training.time}\n"
        f"📍 <b>Место:</b> {training.place}\n"
        "🏢 <b>Формат:</b> Корпоративная\n"
        "\n"
        "Укажи свой ответ 👇"
    )


async def publish_poll(
    bot: Bot,
) -> bool:
    global poll_published

    if poll_published:
        return False

    if poll_cancelled:
        return False

    training = get_training()

    date_text = format_training_date(
        training.date
    )

    training_message = (
        "🏃 <b>Тренировка</b>\n"
        f"📅 <b>Дата:</b> {date_text}\n"
        f"🕐 <b>Время:</b> {training.time}\n"
        f"📍 <b>Место:</b> {training.place}\n"
        "🏢 <b>Формат:</b> Корпоративная\n"
        "\n"
        "Укажи свой ответ 👇"
    )

    await bot.send_message(
        chat_id=settings.group_id,
        message_thread_id=settings.topic_id,
        text=training_message,
        parse_mode="HTML",
    )

    await bot.send_poll(
        chat_id=settings.group_id,
        message_thread_id=settings.topic_id,
        question="Ты будешь на тренировке?",
        options=[
            "✅ Иду.",
            "❌ Не иду.",
            "❓ Под вопросом.",
        ],
        is_anonymous=False,
        allows_multiple_answers=False,
    )

    poll_published = True

    return True
