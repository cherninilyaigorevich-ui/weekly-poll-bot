import logging

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.keyboards import main_keyboard
from app.poll_service import (
    get_preview,
    is_cancelled,
    is_published,
    prepare_week,
    publish_poll,
)


logger = logging.getLogger(__name__)


async def request_confirmation(bot: Bot) -> None:
    prepare_week()

    await bot.send_message(
        chat_id=settings.admin_id,
        text=(
            "🗳 <b>Голосование на следующую тренировку</b>\n\n"
            + get_preview()
            + "\n\n"
            + "<b>Опубликовать?</b>"
        ),
        reply_markup=main_keyboard(),
        parse_mode="HTML",
    )

    logger.info("Weekly poll confirmation sent")


async def remind_admin(bot: Bot) -> None:
    if is_published() or is_cancelled():
        return

    await bot.send_message(
        chat_id=settings.admin_id,
        text=(
            "⏰ <b>Напоминание</b>\n\n"
            "Голосование ещё не опубликовано.\n\n"
            + get_preview()
        ),
        reply_markup=main_keyboard(),
        parse_mode="HTML",
    )

    logger.info("Weekly poll reminder sent")


async def auto_publish(bot: Bot) -> None:
    if is_published() or is_cancelled():
        return

    published = await publish_poll(bot)

    if not published:
        return

    await bot.send_message(
        chat_id=settings.admin_id,
        text="🤖 Голосование автоматически опубликовано.",
    )

    logger.info("Weekly poll automatically published")


def create_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(
        timezone=settings.timezone,
    )

    scheduler.add_job(
        request_confirmation,
        trigger="cron",
        day_of_week="sun",
        hour=13,
        minute=0,
        args=[bot],
        id="weekly_poll_request",
        replace_existing=True,
    )

    scheduler.add_job(
        remind_admin,
        trigger="cron",
        day_of_week="sun",
        hour=16,
        minute=0,
        args=[bot],
        id="weekly_poll_reminder",
        replace_existing=True,
    )

    scheduler.add_job(
        auto_publish,
        trigger="cron",
        day_of_week="sun",
        hour=19,
        minute=0,
        args=[bot],
        id="weekly_poll_auto_publish",
        replace_existing=True,
    )

    return scheduler
