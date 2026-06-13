"""Paths and pydantic settings. OMDb key is required (loaded from .env or env)."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CSV_PATH = PROJECT_ROOT / "revenues_per_day.csv"
DB_PATH = DATA_DIR / "warehouse.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    omdb_api_key: str = Field(min_length=1)        # required, non-empty
    omdb_base_url: str = "https://www.omdbapi.com/"
    omdb_max_workers: int = Field(default=8, ge=1)  # concurrency for the OMDb fetch


settings = Settings()
