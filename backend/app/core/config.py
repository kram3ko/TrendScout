from functools import lru_cache

from pydantic import Field, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.enums import LLMProvider


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_user: str = "trendscout"
    postgres_password: str = "trendscout"
    postgres_db: str = "trendscout"
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    redis_url: str = "redis://redis:6379/0"

    secret_key: str = "change-me-before-exposing-this-service"
    access_token_ttl_minutes: int = 720
    bootstrap_username: str = "admin"
    bootstrap_password: str = "admin123"
    cookie_secure: bool = False

    llm_provider: LLMProvider = LLMProvider.GEMINI
    llm_api_key: str = ""
    llm_model: str = "gemini-3.5-flash-lite"
    llm_batch_size: int = Field(default=10, ge=1, le=25)

    amazon_max_items_per_category: int = Field(default=30, ge=1, le=50)
    scrape_interval_hours: int = Field(default=6, ge=1)
    trends_geo: str = "US"
    trends_max_products_per_run: int = Field(default=20, ge=1)

    cors_origins: str = "http://localhost:5173,http://localhost:8080"

    @computed_field
    @property
    def database_url(self) -> str:
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.postgres_user,
                password=self.postgres_password,
                host=self.postgres_host,
                port=self.postgres_port,
                path=self.postgres_db,
            )
        )

    @computed_field
    @property
    def cors_origin_list(self) -> list[str]:
        return _split_csv(self.cors_origins)

    @computed_field
    @property
    def llm_enabled(self) -> bool:
        return self.llm_provider is not LLMProvider.NONE and bool(self.llm_api_key)


def _split_csv(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
