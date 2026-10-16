#!/bin/bash

CONTAINER="weekly-poll-bot"
ENV_FILE="/opt/weekly-poll-bot/.env"
STATE_FILE="/tmp/weekly-poll-bot-health.state"

BOT_TOKEN=$(grep '^BOT_TOKEN=' "$ENV_FILE" | cut -d '=' -f2-)
ADMIN_ID=$(grep '^ADMIN_ID=' "$ENV_FILE" | cut -d '=' -f2-)

STATUS=$(docker inspect \
    -f '{{.State.Status}}' \
    "$CONTAINER" 2>/dev/null)

if [ "$STATUS" = "running" ]; then

    if [ -f "$STATE_FILE" ] && \
       [ "$(cat "$STATE_FILE")" = "down" ]; then

        curl -s \
            -X POST \
            "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
            -d "chat_id=${ADMIN_ID}" \
            --data-urlencode \
            "text=✅ Weekly Poll Bot снова работает." \
            >/dev/null
    fi

    echo "up" > "$STATE_FILE"
    exit 0
fi

if [ ! -f "$STATE_FILE" ] || \
   [ "$(cat "$STATE_FILE")" != "down" ]; then

    curl -s \
        -X POST \
        "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
        -d "chat_id=${ADMIN_ID}" \
        --data-urlencode \
        "text=🚨 Weekly Poll Bot НЕ РАБОТАЕТ!

Состояние контейнера: ${STATUS:-not found}

Сервер: $(hostname)
Время: $(date '+%d.%m.%Y %H:%M:%S')" \
        >/dev/null
fi

echo "down" > "$STATE_FILE"
