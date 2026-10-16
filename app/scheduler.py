import logging
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.config import settings
from app.keyboards import main_keyboard
from app.poll_service import get_preview, prepare_week, publish_poll, status

logger = logging.getLogger(__name__)


async def request_confirmation(bot: Bot):
    prepare_week()
    if status() != "draft":
        logger.info("Sunday request skipped: status=%s", status())
        return
    await bot.send_message(settings.admin_id,
                           "🗳 <b>Голосование на следующую тренировку</b>\n\n" +
                           await get_preview() + "\n\nОпубликовать?",
                           reply_markup=main_keyboard(), parse_mode="HTML")


async def remind_admin(bot: Bot):
    prepare_week()
    if status() != "draft":
        return
    await bot.send_message(settings.admin_id,
                           "⏰ <b>Напоминание</b>\n\n" + await get_preview(),
                           reply_markup=main_keyboard(), parse_mode="HTML")


async def auto_publish(bot: Bot):
    prepare_week()
    if status() != "draft":
        return
    try:
        published = await publish_poll(bot)
        if published:
            await bot.send_message(settings.admin_id, "🤖 Голосование автоматически опубликовано.")
    except Exception:
        logger.exception("Automatic publication failed; inspect Telegram")
        try:
            await bot.send_message(settings.admin_id, "🚨 Не удалось подтвердить публикацию. Проверь группу и /status.")
        except Exception:
            logger.exception("Could not notify admin")


def create_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler(timezone=settings.timezone)
    for name, fn, hour in (("request", request_confirmation, 13),
                           ("reminder", remind_admin, 16),
                           ("auto_publish", auto_publish, 19)):
        scheduler.add_job(fn, "cron", day_of_week="sun", hour=hour, minute=0,
                          args=[bot], id=f"weekly_{name}", replace_existing=True,
                          misfire_grace_time=300, max_instances=1, coalesce=True)
    return scheduler
