# Weekly Poll Bot 🏃

Telegram bot for weekly corporate training attendance polls, with Monday weather forecast and restart-safe publication state.

## Features
- Sunday 13:00 admin confirmation, 16:00 reminder, 19:00 auto-publication (Europe/Moscow).
- Edit training date/time/location; corporate format and non-anonymous Telegram poll.
- Open-Meteo forecast at training hour; weather failures do not block the poll.
- Atomic JSON state in a persistent Docker volume; duplicate publication is blocked across restarts.
- If Telegram request outcome is unknown, bot locks publication in `uncertain` until manually investigated.
- `/poll` or `/status` in admin private chat; `/id` for diagnostics.

## Stack
Python 3.13, aiogram 3, APScheduler 3, httpx, Open-Meteo, Docker Compose, pytest, GitHub Actions.

## Deploy
1. `cp .env.example .env` and set BOT_TOKEN, ADMIN_ID, GROUP_ID, TOPIC_ID. Keep `.env` private.
2. Set accurate `WEATHER_LATITUDE` and `WEATHER_LONGITUDE` for the stadium (defaults are city center).
3. **Before first deployment, inspect the group for an existing poll for the upcoming Monday.** If present, initialize persistent state as `published` (see migration below).
4. `docker compose build && docker compose up -d`
5. `docker compose ps && docker compose logs --tail=50`

## First deployment / migration
The old version kept publication state only in RAM. **Do not start the new version without determining whether this week's poll has already been posted.**

The first deployment creates a named volume. To mark an existing poll as published before starting the bot, use:

```bash
docker compose create
docker compose run --rm --no-deps --entrypoint python weekly-poll-bot -c '
from app.state import store
store.get_or_create()
store.set_status("published")
print(store.state)
'
```

**Important:** `docker compose run` can start the application image only with the Python override above, not the bot. `published` applies only to the upcoming Monday and is automatically reset when the next weekly key changes. If no poll has been published, skip marking it; the first `/poll` creates a draft. Never run `/testpoll` in production; it was removed.

## Safety model
At-most-once *attempt* semantics, not guaranteed exactly-once delivery: Telegram and local JSON cannot participate in one transaction. If the process crashes after Telegram accepts a request but before its acknowledgement, state stays `publishing` or `uncertain` and requires manual reconciliation. Do not reset state blindly.

## Local tests
`pip install -r requirements-dev.txt && pytest -q`

## Monitoring
Keep the existing host-level watchdog (`healthcheck.sh` + cron) outside the container; it can alert when the bot process is down. Docker healthcheck is supplementary and only checks that the process is alive, not Telegram connectivity.

## Privacy
No face recognition or photos are processed by this release. Tokens and personal identifiers are not committed to Git.
