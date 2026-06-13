"""Paths, database URL and OMDb credentials (secrets from env)."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CSV_PATH = PROJECT_ROOT / "revenues_per_day.csv"

DB_PATH = DATA_DIR / "warehouse.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

OMDB_API_KEY = os.getenv("OMDB_API_KEY", "")
OMDB_BASE_URL = "https://www.omdbapi.com/"
