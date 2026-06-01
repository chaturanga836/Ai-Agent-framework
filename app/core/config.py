from functools import lru_cache
from typing import Optional
from urllib.parse import quote_plus

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ELT Agent Service"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8100

    # Full SQLAlchemy URL (preferred). Use postgresql:// on the shared ELT Postgres server.
    database_url: Optional[str] = None

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "elt"
    postgres_password: str = "changeme"
    postgres_db: str = "elt_agent"

    etl_api_url: str = "http://localhost:8000/api/v1"
    etl_api_token: str = ""

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str = ""

    http_timeout_seconds: float = 60.0
    job_timeout_seconds: float = 600.0

    @model_validator(mode="after")
    def resolve_database_url(self) -> "Settings":
        if self.database_url:
            return self
        password = quote_plus(self.postgres_password)
        self.database_url = (
            f"postgresql://{self.postgres_user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
        return self

    @property
    def resolved_database_url(self) -> str:
        return self.database_url or (
            f"postgresql://{self.postgres_user}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
