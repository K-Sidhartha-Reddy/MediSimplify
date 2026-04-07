from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    mongodb_url: str
    mongodb_db_name: str = "medical_report_simplifier"
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    upload_dir: str = "./uploads"
    tesseract_cmd: str = "/opt/homebrew/bin/tesseract"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
