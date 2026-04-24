from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://app_user:changeme@localhost:5432/myapp"

    # Auth
    SECRET_KEY: str = "CHANGE_ME"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS accepts comma-separated values, JSON list strings, or a real list.
    # NoDecode prevents pydantic-settings from JSON-parsing the env value before the
    # validator runs, which would otherwise reject plain comma-separated input.
    CORS_ORIGINS: Annotated[list[str], NoDecode] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:80",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            stripped = v.strip()
            if stripped.startswith("["):
                import json

                return json.loads(stripped)
            return [item.strip() for item in stripped.split(",") if item.strip()]
        return v

    # App
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"


settings = Settings()
