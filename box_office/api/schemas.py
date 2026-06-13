"""Request/response models for the API."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class LoadSummary(BaseModel):
    rows_read: int
    movies_new: int
    omdb_calls: int
    dim_versions_added: int
    fact_revenue_rows: int
    rating_snapshots: int
    dates_added: int
    duration_ms: int


class RefreshScope(str, Enum):
    stale = "stale"
    all = "all"
    ids = "ids"


class RefreshSummary(BaseModel):
    movies_checked: int
    omdb_calls: int
    dim_versions_added: int
    rating_snapshots: int
    duration_ms: int


class HealthStatus(BaseModel):
    status: str
    db_ok: bool
    omdb_key_present: bool
