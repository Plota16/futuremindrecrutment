"""Static, non-environment constants: domain values, seed data, client tuning.

Environment-driven settings (keys, URLs, worker counts) live in `config.py`.
This module holds values fixed by the data model and the OMDb contract.
"""

from __future__ import annotations

# Conventional "Unknown" member; real surrogates autoincrement from 1.
UNKNOWN_ID = 0

# Rating source names — must match OMDb Ratings[].Source verbatim.
# IMDB_SOURCE also carries the vote counts.
IMDB_SOURCE = "Internet Movie Database"
ROTTEN_TOMATOES_SOURCE = "Rotten Tomatoes"
METACRITIC_SOURCE = "Metacritic"

# Rating sources seeded into dim_rating_source.
# (source_id, name, scale_max, scale_unit)
RATING_SOURCES: list[tuple[int, str, int, str]] = [
    (1, IMDB_SOURCE, 10, "decimal"),
    (2, ROTTEN_TOMATOES_SOURCE, 100, "percentage"),
    (3, METACRITIC_SOURCE, 100, "points"),
]

# Credit roles stored in bridge_movie_person.credit_role.
CREDIT_ACTOR = "ACTOR"
CREDIT_DIRECTOR = "DIRECTOR"
CREDIT_WRITER = "WRITER"

# How many rows each ranking shows.
TOP_N = 5

# Weekdays (date.weekday(): Mon=0 … Sun=6) treated as "weekend" for dim_date.
# Friday is included as a weekend day per business definition.
WEEKEND_WEEKDAYS = {4, 5, 6}  # Fri, Sat, Sun

CSV_COLUMNS = ["id", "date", "title", "revenue", "theaters", "distributor"]

# Pool generously so concurrent workers don't queue on connections.
OMDB_POOL_SIZE = 32
OMDB_RETRY_TOTAL = 3
OMDB_RETRY_BACKOFF = 0.5  # 0.5s, 1s, 2s between retries
OMDB_RETRY_STATUSES = (429, 500, 502, 503, 504)
