from __future__ import annotations

from datetime import date
from typing import Optional

from sqlmodel import Field

from .base import DwhTable


class BronzeRevenueCsv(DwhTable, table=True):
    __tablename__ = "bronze_revenue_csv"

    bronze_revenue_id: Optional[int] = Field(default=None, primary_key=True)
    row_uuid: str  # original CSV `id` (not indexed — never queried by it)
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
    found: bool = Field(default=False)  # OMDb "Response"
    response_json: str
