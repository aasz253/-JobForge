"""Application settings — loaded from environment / `.env` (never from code)."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "JOBFORGE"
    app_tagline: str = "Find. Qualify. Apply. Advance."
    app_made_by: str = "Sifuna Codex"
    environment: str = "dev"
    api_prefix: str = "/api"

    # Core
    database_url: str = "sqlite:///./jobforge.db"
    secret_key: str = "change-me-to-a-long-random-string"  # override in .env
    session_lifetime: int = 7 * 24 * 3600

    # CORS
    cors_origins: str = "http://localhost:3000"

    # AI
    ai_provider: str = "none"  # none | local | openai_compatible | openrouter
    ai_base_url: str = ""
    ai_api_key: str = ""
    ai_model: str = ""
    ai_model_ring: str = ""  # comma-separated OpenRouter free models, tried in order
    ai_fallback_local: bool = False  # fall back to local Ollama when the ring is unreachable
    ai_disabled: bool = False

    # Integrations
    github_token: str = ""
    github_mode: str = "public"

    email_client_id: str = ""
    email_client_secret: str = ""
    email_redirect_uri: str = "http://localhost:8000/api/email/callback"

    # Field encryption (Fernet key)
    field_encryption_key: str = ""

    # Security
    allowed_hosts: str = ""
    rate_limit_login: int = 20
    rate_limit_login_window: int = 300
    rate_limit_import: int = 30
    rate_limit_import_window: int = 600
    rate_limit_global_per_minute: int = 300

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def ai_configured(self) -> bool:
        return not self.ai_disabled and bool(self.ai_base_url) and self.ai_provider in ("local", "openai_compatible")


@lru_cache
def get_settings() -> Settings:
    return Settings()