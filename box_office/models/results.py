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
    dates_added: int
    movies: int
    fact_revenue_rows: int


@dataclass
class SilverEnrichmentResult:
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
