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
