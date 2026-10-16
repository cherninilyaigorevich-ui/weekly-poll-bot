from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    admin_id: int
    group_id: int
    topic_id: int
    timezone: str = "UTC"
    default_time: str = "18:00"
    default_place: str = "Training venue"
    weather_latitude: float = 0.0  # Configure actual venue coordinates in private .env
    weather_longitude: float = 0.0
    weather_enabled: bool = True
    state_path: str = "/data/state.json"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
