# api/core/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str

    OPENROUTER_API_KEY: str
    OPENROUTER_MODEL: str = "meta-llama/llama-3.3-8b-instruct:free"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_SITE_URL: str = "http://localhost:3000"
    OPENROUTER_APP_NAME: str = "Termcraft AI"

    # AI Service Configuration
    PRIMARY_AI_SERVICE: str = "ollama"  # "ollama" or "openrouter"
    
    FRONTEND_ORIGIN: str = "http://localhost:5003"

settings = Settings()  # singleton import
