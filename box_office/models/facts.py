from __future__ import annotations

from typing import Optional

from sqlmodel import Field

from .base import DwhTable


class FactDailyRevenue(DwhTable, table=True):
    __tablename__ = "fact_daily_revenue"

    date_id: int = Field(primary_key=True, foreign_key="dim_date.date_id")
    movie_version_id: int = Field(primary_key=True,
                                  foreign_key="dim_movie.movie_version_id")
    revenue: int
    theaters: Optional[int] = None


class FactMovieRating(DwhTable, table=True):
    __tablename__ = "fact_movie_rating"

    movie_id: int = Field(primary_key=True,
                          index=True)  # durable ref, no FK (target non-unique)
    source_id: int = Field(primary_key=True,
                           foreign_key="dim_rating_source.source_id")
    snapshot_date_id: int = Field(primary_key=True,
                                  foreign_key="dim_date.date_id")
    rating_value_native: float
    votes: Optional[int] = None
