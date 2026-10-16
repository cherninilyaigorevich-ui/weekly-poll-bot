from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    admin_id: int
    group_id: int
    topic_id: int
    timezone: str = "Europe/Moscow"
    default_time: str = "19:30"
    default_place: str = 'Стадион "Шторм"'
    weather_latitude: float = 59.9343  # Санкт-Петербург; уточните координаты стадиона
    weather_longitude: float = 30.3351
    weather_enabled: bool = True
    state_path: str = "/data/state.json"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
