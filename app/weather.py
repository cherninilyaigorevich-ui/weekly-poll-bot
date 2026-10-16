"""Open-Meteo forecast with bounded retries and graceful fallback."""
import asyncio
import logging
from datetime import date

import httpx

from app.config import settings

logger = logging.getLogger(__name__)
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
    async with httpx.AsyncClient(timeout=5) as client:
        for attempt in range(2):
            try:
                response = await client.get("https://api.open-meteo.com/v1/forecast", params=params)
                response.raise_for_status()
                return parse_forecast(response.json(), target, hour)
            except (httpx.HTTPError, KeyError, ValueError, TypeError) as exc:
                logger.warning("Weather request failed (attempt %s): %s", attempt + 1, type(exc).__name__)
                if attempt == 0:
                    await asyncio.sleep(0.5)
    return None
