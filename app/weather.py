"""Open-Meteo forecast with bounded retries and graceful fallback."""
import asyncio
import logging
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from datetime import date

import httpx

from app.config import settings

logger = logging.getLogger(__name__)
CACHE_MAX_AGE = timedelta(hours=3)
RETRY_DELAYS = (2, 5, 10)


def _cache_path() -> Path:
    return Path(settings.state_path).with_name('weather_cache.json')


def _cached_forecast(target: date, hour: int) -> str | None:
    try:
        data = json.loads(_cache_path().read_text(encoding='utf-8'))
        saved = datetime.fromisoformat(data['saved_at'])
        if (data['date'] == target.isoformat() and data['hour'] == hour
                and datetime.now(timezone.utc) - saved < CACHE_MAX_AGE):
            return data['text']
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return None


def _save_forecast(target: date, hour: int, text: str) -> None:
    path = _cache_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix('.tmp')
        temp.write_text(json.dumps({'date': target.isoformat(), 'hour': hour,
                                    'saved_at': datetime.now(timezone.utc).isoformat(),
                                    'text': text}, ensure_ascii=False), encoding='utf-8')
        os.replace(temp, path)
    except OSError:
        logger.warning('Weather cache write failed')

WMO = {
    0: "ясно", 1: "преимущественно ясно", 2: "переменная облачность",
    3: "пасмурно", 45: "туман", 48: "туман", 51: "морось",
    53: "морось", 55: "морось", 61: "небольшой дождь",
    63: "дождь", 65: "сильный дождь", 71: "небольшой снег",
    73: "снег", 75: "сильный снег", 80: "ливень",
    81: "ливень", 82: "сильный ливень", 95: "гроза",
    96: "гроза с градом", 99: "гроза с градом",
}


def parse_forecast(data: dict, target: date, hour: int) -> str:
    hourly = data["hourly"]
    stamps = hourly["time"]
    key = f"{target.isoformat()}T{hour:02d}:00"
    index = stamps.index(key)
    temp = round(hourly["temperature_2m"][index])
    code = hourly["weather_code"][index]
    wind_kmh = hourly["wind_speed_10m"][index]
    precip = hourly["precipitation_probability"][index]
    return (f"🌤 <b>Прогноз на тренировку:</b> {WMO.get(code, 'переменная погода')}\n"
            f"🌡 {temp:+d} °C · 💧 вероятность осадков {precip}% · "
            f"💨 {wind_kmh / 3.6:.1f} м/с")


async def get_weather(target: date, time: str) -> str | None:
    if not settings.weather_enabled:
        return None
    try:
        hour = int(time.split(":")[0])
    except (ValueError, IndexError):
        return None
    params = {
        "latitude": settings.weather_latitude,
        "longitude": settings.weather_longitude,
        "hourly": "temperature_2m,precipitation_probability,weather_code,wind_speed_10m",
        "timezone": settings.timezone,
        "start_date": target.isoformat(),
        "end_date": target.isoformat(),
    }
    async with httpx.AsyncClient(timeout=8) as client:
        for attempt in range(len(RETRY_DELAYS) + 1):
            try:
                response = await client.get("https://api.open-meteo.com/v1/forecast", params=params)
                response.raise_for_status()
                forecast = parse_forecast(response.json(), target, hour)
                _save_forecast(target, hour, forecast)
                return forecast
            except (httpx.HTTPError, KeyError, ValueError, TypeError) as exc:
                logger.warning("Weather request failed (attempt %s): %s", attempt + 1, type(exc).__name__)
                if attempt < len(RETRY_DELAYS):
                    await asyncio.sleep(RETRY_DELAYS[attempt])
    cached = _cached_forecast(target, hour)
    if cached:
        logger.info('Using recent cached forecast for %s %02d:00', target, hour)
    return cached
