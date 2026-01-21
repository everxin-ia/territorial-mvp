# app/core/config.py
from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = BACKEND_ROOT / ".env"


class Settings(BaseSettings):
    env: str = "dev"
    database_url: str

    alert_webhook_url: str | None = None

    # Scheduler / jobs
    # DISABLE_SCHEDULER=true para evitar jobs en startup
    disable_scheduler: bool = False

    # IA
    ai_provider: str | None = "openai"
    openai_api_key: str | None = None
    openai_model: str | None = "gpt-4o-mini"
    openai_base_url: str | None = "https://api.openai.com/v1"

    anthropic_api_key: str | None = None
    anthropic_model: str | None = None

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH) if ENV_PATH.exists() else None,
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
