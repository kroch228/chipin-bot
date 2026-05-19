from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str = ""
    database_url: str = "sqlite+aiosqlite:///data/chipin.db"
    log_level: str = "INFO"
    default_locale: str = "ru"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
