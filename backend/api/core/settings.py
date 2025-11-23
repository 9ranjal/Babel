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

    # Embeddings/worker flags
    EMBEDDINGS_ENABLED: bool = True
    JOB_POLL_INTERVAL_MS: int = 500
    AUTO_START_WORKER: bool = True
    WORKER_PARALLELISM: int = 2
    WORKER_STALE_SECONDS: int = 120
    WORKER_STALE_JOB_SECONDS: int = 300
    WORKER_STALE_CHECK_INTERVAL_SECONDS: int = 60
    DB_SCHEMA: str = "public"


settings = Settings()

def get_demo_user_id() -> str:
    return settings.DEMO_USER_ID
