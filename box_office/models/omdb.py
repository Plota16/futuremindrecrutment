"""OMDb data structures: raw fetch result, parsed movie, fetch stats."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class OmdbResult:
    found: bool
    raw_json: str       # exact response body, stored verbatim in bronze


@dataclass
class OmdbFetchStats:
    requested: int
    skipped_cached: int
    calls: int
    found: int
    not_found: int


@dataclass
class ParsedRating:
    source_name: str        # matches dim_rating_source.source_name
    value_native: float


@dataclass
class ParsedMovie:
    title: str
    released_date: Optional[date]
    runtime_min: Optional[int]
    plot: Optional[str]
    language: Optional[str]
    country: Optional[str]
    genres: list[str]
    persons: list[tuple[str, str]]   # (name, role)
    ratings: list[ParsedRating]
    votes: Optional[int]
