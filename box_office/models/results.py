"""ETL result/summary dataclasses."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BronzeResult:
    rows_read: int
    omdb_requested: int
    omdb_calls: int
    omdb_found: int
    omdb_not_found: int


@dataclass
class SilverCoreResult:
    """Silver built from the CSV bronze only (no API dependency)."""

    dates_added: int
    movies: int
    fact_revenue_rows: int


@dataclass
class SilverEnrichmentResult:
    """Silver built from whatever is currently in the OMDb bronze cache."""

    movies_enriched: int
    rating_snapshots: int


@dataclass
class SilverResult:
    dates_added: int
    movies: int
    fact_revenue_rows: int
    rating_snapshots: int


@dataclass
class RefreshResult:
    movies_checked: int
    omdb_calls: int
    omdb_found: int
    rating_snapshots: int
    fact_revenue_rows: int


@dataclass
class LoadResult:
    bronze: BronzeResult
    silver: SilverResult
