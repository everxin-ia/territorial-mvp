from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    env: str = "dev"
    database_url: str

    alert_webhook_url: str | None = None

    # Configuración de IA para geosparsing (opcional)
    ai_provider: str | None = None  # "openai" o "anthropic"
    openai_api_key: str | None = None
    openai_model: str | None = None
    anthropic_api_key: str | None = None
    anthropic_model: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
