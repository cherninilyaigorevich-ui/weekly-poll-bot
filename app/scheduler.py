import logging

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.keyboards import main_keyboard
from app.poll_service import (
    get_preview,
    is_pending,
    prepare_week,
    publish_poll,
)


logger = logging.getLogger(__name__)


async def request_confirmation(
    bot: Bot,
) -> None:
    prepare_week()

    await bot.send_message(
        chat_id=settings.admin_id,
        text=(
            "🗳 <b>Голосование на следующую тренировку</b>\n\n"
            f"{get_preview()}\n\n"
            "Опубликовать голосование?"
        ),
        reply_markup=main_keyboard(),
        parse_mode="HTML",
    )

    logger.info(
        "13:00 - confirmation request sent to admin"
    )


async def remind_admin(
    bot: Bot,
) -> None:
    if not is_pending():
        logger.info(
            "16:00 - reminder skipped: "
            "poll already published or cancelled"
        )
        return

    await bot.send_message(
        chat_id=settings.admin_id,
        text=(
            "⏰ <b>Напоминание</b>\n\n"
            "Голосование ещё не опубликовано.\n\n"
            f"{get_preview()}\n\n"
            "Опубликовать голосование?"
        ),
        reply_markup=main_keyboard(),
        parse_mode="HTML",
    )

    logger.info(
        "16:00 - reminder sent to admin"
    )


async def auto_publish(
    bot: Bot,
) -> None:
    if not is_pending():
        logger.info(
            "19:00 - auto publish skipped: "
            "poll already published or cancelled"
        )
        return

    published = await publish_poll(bot)

    if not published:
        logger.warning(
            "19:00 - automatic publication failed"
        )
        return

    await bot.send_message(
        chat_id=settings.admin_id,
        text=(
            "🤖 <b>Голосование автоматически опубликовано.</b>\n\n"
            "Ответ от администратора не был получен до 19:00."
        ),
        parse_mode="HTML",
    )

    logger.info(
        "19:00 - poll automatically published"
    )


def create_scheduler(
    bot: Bot,
) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(
        timezone=settings.timezone,
    )

    scheduler.add_job(
        request_confirmation,
        trigger="cron",
        day_of_week="sun",
        hour=13,
        minute=0,
        second=0,
        args=[bot],
        id="weekly_poll_request",
        replace_existing=True,
        misfire_grace_time=300,
    )

    scheduler.add_job(
        remind_admin,
        trigger="cron",
        day_of_week="sun",
        hour=16,
        minute=0,
        second=0,
        args=[bot],
        id="weekly_poll_reminder",
        replace_existing=True,
        misfire_grace_time=300,
    )

    scheduler.add_job(
        auto_publish,
        trigger="cron",
        day_of_week="sun",
        hour=19,
        minute=0,
        second=0,
        args=[bot],
        id="weekly_poll_auto_publish",
        replace_existing=True,
        misfire_grace_time=300,
    )

    return scheduler
