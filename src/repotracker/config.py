import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn, AnyHttpUrl


class Settings(BaseSettings):
    """
    Application configuration, loaded from .env file.
    """

    model_config = SettingsConfigDict(
        env_file=(".env"), env_file_encoding="utf-8", extra="ignore"
    )

    database_url: PostgresDsn = Field(..., validation_alias="DATABASE_URL")

    github_api_token: str | None = Field(None, validation_alias="GITHUB_API_TOKEN")

    log_level: str = Field("INFO", validation_alias="LOG_LEVEL")

    github_api_base_url: AnyHttpUrl = Field(
        "https://api.github.com", validation_alias="GITHUB_API_BASE_URL"
    )


settings = Settings()
