"""Paths and pydantic settings. OMDb key required (from .env or env)."""

from __future__ import annotations

from functools import lru_cache
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
        env_file=PROJECT_ROOT / ".env", env_file_encoding="utf-8",
        extra="ignore"
    )

    omdb_api_key: str = Field(min_length=1)
    omdb_base_url: str = "https://www.omdbapi.com/"
    omdb_max_workers: int = Field(default=8, ge=1)


@lru_cache
def get_settings() -> Settings:
    """Lazily build (and cache) Settings.

    Deferred so importing this module — and everything that transitively
    imports it — doesn't require a valid OMDB_API_KEY. Tests and OMDb-free
    code paths can run without the key; the env is only read on first call.
    """
    return Settings()
