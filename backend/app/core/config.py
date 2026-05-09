from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "resumes2ai-backend"
    app_version: str = "0.1.0"
    environment: str = "local"

    database_url: str = f"sqlite:///{ROOT_DIR / 'data' / 'resumes2ai.db'}"
    upload_dir: Path = ROOT_DIR / "uploads"
    data_dir: Path = ROOT_DIR / "data"

    ai_provider: str = "openai_compatible"
    ai_base_url: str = ""
    ai_api_key: str = ""
    ai_model: str = ""
    ai_timeout_seconds: int = 60

    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
