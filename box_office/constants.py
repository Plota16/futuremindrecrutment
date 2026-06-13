"""Static, non-environment constants: domain values, seed data, client tuning.

Environment-driven settings (keys, URLs, worker counts) live in `config.py`.
This module holds values that are fixed by the data model and the OMDb contract.
"""

from __future__ import annotations

# --- Warehouse dimensions ------------------------------------------------

# Conventional "Unknown" dimension member; real surrogates autoincrement from 1.
UNKNOWN_ID = 0

# Rating sources seeded into dim_rating_source.
# (source_id, name, scale_max, scale_unit) — name matches OMDb Ratings[].Source.
RATING_SOURCES: list[tuple[int, str, int, str]] = [
    (1, "Internet Movie Database", 10, "decimal"),
    (2, "Rotten Tomatoes", 100, "percentage"),
    (3, "Metacritic", 100, "points"),
]

# The rating source that carries IMDb vote counts.
IMDB_SOURCE = "Internet Movie Database"

# --- Bronze CSV landing --------------------------------------------------

CSV_COLUMNS = ["id", "date", "title", "revenue", "theaters", "distributor"]

# --- OMDb HTTP client tuning ---------------------------------------------

# Pool generously so concurrent workers don't queue on connections.
OMDB_POOL_SIZE = 32
OMDB_RETRY_TOTAL = 3
OMDB_RETRY_BACKOFF = 0.5  # 0.5s, 1s, 2s between retries
OMDB_RETRY_STATUSES = (429, 500, 502, 503, 504)
