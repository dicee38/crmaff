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

    rate_limit_public_per_minute: int = 60

    sentry_dsn: str = ""

    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def assert_secrets_configured(self) -> None:
        """Отказываем в старте вне development, если секреты остались
        плейсхолдерами - иначе JWT/webhook-подписи подделываются тривиально.
        Секреты - только через env/secret manager (NFR из CLAUDE.md)."""
        if self.environment == "development":
            return
        placeholder_fields = {
            "jwt_secret_key": self.jwt_secret_key,
            "binolla_webhook_secret": self.binolla_webhook_secret,
            "chatterfy_webhook_secret": self.chatterfy_webhook_secret,
            "track_click_signing_secret": self.track_click_signing_secret,
        }
        insecure = [
            name
            for name, value in placeholder_fields.items()
            if value.startswith("change-me") or len(value) < 16
        ]
        if insecure:
            raise RuntimeError(
                f"Небезопасные значения секретов для environment={self.environment!r}: {insecure}. "
                "Задайте реальные случайные значения через env/secret manager перед запуском."
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
