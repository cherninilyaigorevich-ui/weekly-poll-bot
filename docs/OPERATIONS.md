# Operations and recovery

## Verify deployment

```bash
docker compose ps
docker compose logs --tail=100 weekly-poll-bot
docker compose exec weekly-poll-bot sh -c 'ls -l /data/state.json && cat /data/state.json'
```

Expected state for an unpublished upcoming poll: `"status": "draft"`. The volume survives container recreation.

## First deployment from the legacy in-memory version

1. Inspect the target Telegram group and confirm whether a poll for the upcoming Monday has already been published.
2. If **no poll exists**, start the new version normally. It will create a draft when first needed.
3. If **a poll already exists**, initialize the persistent state to `published` **before starting the active bot**:

```bash
docker compose build
docker compose create
docker compose run --rm --no-deps --entrypoint python weekly-poll-bot -c '
from app.state import store
store.get_or_create()
store.set_status("published")
print(store.state)
'
docker compose up -d --no-deps weekly-poll-bot
```

Never run a second active polling process against the same bot token.

## Investigating publication failures

The state machine is intentionally conservative:
- `draft`: not yet published; may be edited or published.
- `publishing`: a publication attempt started. If it persists after restart, inspect Telegram before any recovery.
- `published`: confirmed successful publication.
- `uncertain`: Telegram API request failed or returned an ambiguous result. Check the group and logs before manually reconciling.
- `cancelled`: admin cancelled the week's poll.

Do not reset `publishing` or `uncertain` to `draft` without verifying whether Telegram accepted the poll. The JSON state is not an exactly-once transaction log.

## Backup

Back up `/data/state.json` from the container or its Docker named volume. Treat it as operational data; do not commit it. Prefer a consistent backup outside the container, and restore only with the bot stopped.

## Health monitoring

The Compose healthcheck confirms that the container's main process exists. It does not probe the Telegram API or the scheduler. Keep independent host monitoring and alerting where required.
