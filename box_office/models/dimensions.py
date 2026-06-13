"""Silver layer — dimensions."""

from __future__ import annotations

from datetime import date
from typing import Optional

from sqlmodel import Field

from .base import DwhTable


class DimDate(DwhTable, table=True):
    __tablename__ = "dim_date"

    date_id: int = Field(primary_key=True,
                         sa_column_kwargs={"autoincrement": False})
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
    __tablename__ = "dim_movie"

    movie_id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True, unique=True)
    released_date: Optional[date] = None
    runtime_min: Optional[int] = None
    plot: Optional[str] = None
    language: Optional[str] = None
    country: Optional[str] = None
