import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.handlers import router
from app.scheduler import create_scheduler


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
    )

    bot = Bot(
        token=settings.bot_token,
    )

    dp = Dispatcher(
        storage=MemoryStorage(),
    )

    dp.include_router(router)

    scheduler = create_scheduler(bot)
    scheduler.start()

    logging.info(
        "Weekly Poll Bot started"
    )

    logging.info(
        "Weekly schedule: "
        "Sunday 13:00 -> request, "
        "16:00 -> reminder, "
        "19:00 -> automatic publication"
    )

    try:
        await dp.start_polling(bot)

    finally:
        scheduler.shutdown(
            wait=False
        )

        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
