"""bronze_revenue_csv — CSV landing + revenue reads."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

import pandas as pd
from sqlalchemy import func, text
from sqlmodel import Session, select

from ...constants import CSV_COLUMNS
from ...models import BronzeRevenueCsv
from ...models.base import utcnow

logger = logging.getLogger(__name__)

_UPSERT_COLS = [
    "row_uuid", "event_date", "title", "revenue",
    "theaters", "distributor", "source_file", "load_timestamp",
]
_TMP = "_bronze_revenue_tmp"


class BronzeRevenue:
    def __init__(self, session: Session):
        self.session = session

    def load_csv(
            self, path: str | Path, source_name: str | None = None
    ) -> int:
        """Upsert the CSV into bronze_revenue_csv on grain (event_date, title).

        The UNIQUE constraint on (event_date, title) means a revised report
        for the same day+film replaces the existing row rather than
        accumulating. Within the incoming file, duplicates on the same grain
        are resolved by keeping the last occurrence.

        `source_name` is stored in source_file for audit traceability; it
        should be the original client filename, not a temp-file path.
        """
        name = source_name or Path(path).name
        df = pd.read_csv(path, usecols=CSV_COLUMNS, parse_dates=["date"])
        df = df.rename(columns={"id": "row_uuid", "date": "event_date"})
        df["event_date"] = df["event_date"].dt.date
        df["source_file"] = name
        df["load_timestamp"] = utcnow()

        # Deduplicate within the file on the target grain before upserting.
        df = df.drop_duplicates(subset=["event_date", "title"], keep="last")
        total = len(df)
        logger.info("csv load: start (%d rows from %s)", total, name)

        conn = self.session.connection()

        # Stage into a throw-away temp table, then INSERT OR REPLACE into
        # the real table so the UNIQUE constraint resolves conflicts atomically.
        df[_UPSERT_COLS].to_sql(_TMP, conn, if_exists="replace", index=False)
        cols = ", ".join(_UPSERT_COLS)
        conn.execute(text(
            f"INSERT OR REPLACE INTO {BronzeRevenueCsv.__tablename__}"
            f" ({cols}) SELECT {cols} FROM {_TMP}"
        ))
        conn.execute(text(f"DROP TABLE IF EXISTS {_TMP}"))

        self.session.flush()
        logger.info("csv load: done (%d rows)", total)
        return total

    def distinct_titles(self) -> list[str]:
        return list(
            self.session.exec(select(BronzeRevenueCsv.title).distinct()).all()
        )

    def titles_by_revenue(self) -> list[str]:
        """Distinct titles ordered by total revenue, descending.

        Drives OMDb enrichment priority: under a daily quota the
        highest-earning movies get enriched first; the tail backfills later.
        """
        rows = self.session.exec(
            select(BronzeRevenueCsv.title)
            .group_by(BronzeRevenueCsv.title)
            .order_by(func.sum(BronzeRevenueCsv.revenue).desc())
        ).all()
        return list(rows)

    def distinct_distributors(self) -> list[str]:
        rows = self.session.exec(
            select(BronzeRevenueCsv.distributor).distinct()
        ).all()
        return [d for d in rows if d]

    def distinct_event_dates(self) -> list[date]:
        return list(
            self.session.exec(
                select(BronzeRevenueCsv.event_date).distinct()
            ).all()
        )
