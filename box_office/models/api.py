"""API request/response models."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class CsvLoadSummary(BaseModel):
    rows_read: int
    duration_ms: int


class OmdbLoadSummary(BaseModel):
    omdb_requested: int
    omdb_skipped_cached: int
    omdb_calls: int
    omdb_found: int
    omdb_not_found: int
    duration_ms: int


class SilverSummary(BaseModel):
    dates_added: int
    movies: int
    fact_revenue_rows: int
    movies_enriched: int
    rating_snapshots: int
    duration_ms: int


class LoadSummary(BaseModel):
    rows_read: int
    omdb_calls: int
    omdb_found: int
    omdb_not_found: int
    dates_added: int
    movies: int
    fact_revenue_rows: int
    rating_snapshots: int
    duration_ms: int


class RefreshScope(str, Enum):
    stale = "stale"
    all = "all"
    ids = "ids"


class RefreshSummary(BaseModel):
    movies_checked: int
    omdb_calls: int
    omdb_found: int
    rating_snapshots: int
    fact_revenue_rows: int
    duration_ms: int


class HealthStatus(BaseModel):
    status: str
    db_ok: bool
    omdb_key_present: bool
