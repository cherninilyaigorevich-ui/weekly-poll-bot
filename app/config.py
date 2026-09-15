from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    admin_id: int
    group_id: int
    topic_id: int

    timezone: str = "Europe/Moscow"

    default_time: str = "19:30"
    default_place: str = 'Стадион "Шторм"'

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
