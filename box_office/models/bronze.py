from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field

from .base import DwhTable


class BronzeRevenueCsv(DwhTable, table=True):
    __tablename__ = "bronze_revenue_csv"
    __table_args__ = (
        UniqueConstraint("event_date", "title",
                         name="uq_bronze_revenue_date_title"),
    )

    bronze_revenue_id: Optional[int] = Field(default=None, primary_key=True)
    row_uuid: str
    event_date: date
    title: str = Field(index=True)
    revenue: int
    theaters: Optional[int] = None
    distributor: Optional[str] = None
    source_file: str


class BronzeOmdbRaw(DwhTable, table=True):
    __tablename__ = "bronze_omdb_raw"

    bronze_omdb_id: Optional[int] = Field(default=None, primary_key=True)
    title_queried: str = Field(index=True)
    found: bool = Field(default=False)
    response_json: str
