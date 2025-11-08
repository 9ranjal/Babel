"""Runtime configuration for the minimalist API."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[3]
ENV_FILE = BASE_DIR / "backend" / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "deepseek/deepseek-chat-v3.1"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_SITE_URL: str = "http://localhost:3000"
    OPENROUTER_APP_NAME: str = "Babel Copilot"

    FRONTEND_ORIGIN: str = "http://localhost:3000,http://localhost:5003"

    # Supabase (backend only)
    SUPABASE_DB_URL: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # Dev-only: single demo user scope
    DEMO_USER_ID: str = "00000000-0000-0000-0000-000000000001"


settings = Settings()

def get_demo_user_id() -> str:
    return settings.DEMO_USER_ID
