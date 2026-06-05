from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


API_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "skin-care-companion-api"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    database_path: Path = API_ROOT / "storage" / "skin_care.db"
    upload_dir: Path = API_ROOT / "storage" / "tmp_uploads"

    youcam_mode: str = "mock"
    youcam_api_key: str | None = None
    youcam_endpoint: str | None = None
    external_api_timeout_sec: float = 20.0

    llm_api_key: str | None = None
    discord_webhook_url: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()

