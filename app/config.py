from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"

    database_url: str = "postgresql+asyncpg://crm:crm@localhost:5432/crm"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str = "change-me-to-a-random-secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    binolla_webhook_secret: str = "change-me"
    chatterfy_webhook_secret: str = "change-me"
    track_click_signing_secret: str = "change-me"

    chatterfy_api_base_url: str = ""
    chatterfy_api_key: str = ""

    sentry_dsn: str = ""

    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
