from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ASYNC_DATABASE_URL_PREFIX = "postgresql+asyncpg://"


class Settings(BaseSettings):
    database_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("database_url")
    @classmethod
    def require_async_postgres_url(cls, value: str) -> str:
        if not value.startswith(ASYNC_DATABASE_URL_PREFIX):
            raise ValueError(
                f"database_url must start with {ASYNC_DATABASE_URL_PREFIX!r}; "
                "the backend uses SQLAlchemy's async API with asyncpg"
            )
        return value


@lru_cache
def get_settings() -> Settings:
    """Load and validate settings on first use.

    Nothing is read at import time. The application validates settings during
    startup, and tests can replace this dependency through
    `app.dependency_overrides[get_settings]`.
    """
    # pydantic-settings fills required fields from the environment at runtime;
    # mypy only sees the missing constructor argument.
    return Settings()  # type: ignore[call-arg]
