from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    env: str = "dev"
    database_url: str

    alert_webhook_url: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
