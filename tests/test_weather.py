from datetime import date
from app.weather import parse_forecast


def test_parse_forecast():
    data = {"hourly": {"time": ["2026-10-19T19:00"],
                       "temperature_2m": [8.4], "weather_code": [61],
                       "wind_speed_10m": [18], "precipitation_probability": [40]}}
    text = parse_forecast(data, date(2026, 10, 19), 19)
    assert "+8 °C" in text
    assert "5.0 м/с" in text
    assert "40%" in text
