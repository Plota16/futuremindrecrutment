"""Silver layer — facts."""

from __future__ import annotations

from typing import Optional

from sqlmodel import Field

from .base import DwhTable


class FactDailyRevenue(DwhTable, table=True):
    __tablename__ = "fact_daily_revenue"

    date_id: int = Field(primary_key=True, foreign_key="dim_date.date_id")
    movie_id: int = Field(primary_key=True, foreign_key="dim_movie.movie_id")
    distributor_id: Optional[int] = Field(default=None, foreign_key="dim_distributor.distributor_id")
    revenue: int
    theaters: Optional[int] = None


class FactMovieRating(DwhTable, table=True):
    __tablename__ = "fact_movie_rating"

    movie_id: int = Field(primary_key=True, foreign_key="dim_movie.movie_id")
    source_id: int = Field(primary_key=True, foreign_key="dim_rating_source.source_id")
    snapshot_date_id: int = Field(primary_key=True, foreign_key="dim_date.date_id")
    rating_value_native: float
    votes: Optional[int] = None
