from __future__ import annotations

from datetime import date
from typing import Optional

from sqlmodel import Field

from .base import DwhTable


class DimDate(DwhTable, table=True):
    __tablename__ = "dim_date"

    date_id: int = Field(primary_key=True,
                         sa_column_kwargs={"autoincrement": False})  # YYYYMMDD
    full_date: date = Field(index=True, unique=True)
    is_weekend: bool = Field(default=False)
    is_holiday: bool = Field(default=False)
    holiday_name: Optional[str] = None


class DimDistributor(DwhTable, table=True):
    __tablename__ = "dim_distributor"

    distributor_id: Optional[int] = Field(default=None, primary_key=True)
    distributor_name: str = Field(index=True, unique=True)


class DimRatingSource(DwhTable, table=True):
    __tablename__ = "dim_rating_source"

    source_id: int = Field(primary_key=True,
                           sa_column_kwargs={"autoincrement": False})
    source_name: str = Field(index=True, unique=True)
    scale_max: int
    scale_unit: str


class DimGenre(DwhTable, table=True):
    __tablename__ = "dim_genre"

    genre_id: Optional[int] = Field(default=None, primary_key=True)
    genre_name: str = Field(index=True, unique=True)


class DimPerson(DwhTable, table=True):
    __tablename__ = "dim_person"

    person_id: Optional[int] = Field(default=None, primary_key=True)
    person_name: str = Field(index=True, unique=True)


class DimMovie(DwhTable, table=True):
    """SCD2: movie_version_id = version PK, movie_id = durable key."""

    __tablename__ = "dim_movie"

    movie_version_id: Optional[int] = Field(default=None, primary_key=True)
    movie_id: int = Field(index=True)  # durable, not unique under SCD2
    title: str = Field(index=True)
    year_num: Optional[int] = None
    rated: Optional[str] = None
    released_date: Optional[date] = None
    runtime_min: Optional[int] = None
    plot: Optional[str] = None
    language: Optional[str] = None
    country: Optional[str] = None
    poster_url: Optional[str] = None
    distributor_id: Optional[int] = Field(default=None,
                                          foreign_key="dim_distributor.distributor_id")
    valid_from: date
    valid_to: date
    is_current: bool = Field(default=True, index=True)
