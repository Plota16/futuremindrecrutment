"""RevenueRepository — data access for bronze_revenue_csv."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

import pandas as pd
from sqlalchemy import delete, func
from sqlmodel import Session, select

from ..constants import CSV_COLUMNS
from ..models import BronzeRevenueCsv
from ..models.base import utcnow

logger = logging.getLogger(__name__)


class RevenueRepository:
    def __init__(self, session: Session):
        self.session = session

    def load_csv(self, path: str | Path) -> int:
        """Load the CSV 1:1 into bronze_revenue_csv (re-load replaces)."""
        name = Path(path).name
        df = pd.read_csv(path, usecols=CSV_COLUMNS, parse_dates=["date"])
        df = df.rename(columns={"id": "row_uuid", "date": "event_date"})
        df["event_date"] = df["event_date"].dt.date
        df["source_file"] = name
        df["load_timestamp"] = utcnow()

        total = len(df)
        logger.info("csv load: start (%d rows from %s)", total, name)
        self.session.execute(delete(BronzeRevenueCsv).where(
            BronzeRevenueCsv.source_file == name))

        table = BronzeRevenueCsv.__tablename__
        conn = self.session.connection()
        step = max(1, total // 20)  # ~5% chunks
        for start in range(0, total, step):
            df.iloc[start: start + step].to_sql(table, conn,
                                                if_exists="append",
                                                index=False)
            done = min(start + step, total)
            logger.info("csv rows %d/%d (%d%%)", done, total,
                        done * 100 // total)

        self.session.flush()
        logger.info("csv load: done (%d rows)", total)
        return total

    def distinct_titles(self) -> list[str]:
        return list(
            self.session.exec(select(BronzeRevenueCsv.title).distinct()).all())

    def titles_by_revenue(self) -> list[str]:
        """Distinct titles ordered by total revenue, descending.

        Drives the OMDb enrichment priority: under a daily API quota, the
        highest-earning movies (the ones the ranking dashboard cares about) get
        enriched first; the long tail backfills on later runs.
        """
        rows = self.session.exec(
            select(BronzeRevenueCsv.title)
            .group_by(BronzeRevenueCsv.title)
            .order_by(func.sum(BronzeRevenueCsv.revenue).desc())
        ).all()
        return list(rows)

    def distinct_distributors(self) -> list[str]:
        rows = self.session.exec(
            select(BronzeRevenueCsv.distributor).distinct()).all()
        return [d for d in rows if d]

    def distinct_event_dates(self) -> list[date]:
        return list(self.session.exec(
            select(BronzeRevenueCsv.event_date).distinct()).all())
