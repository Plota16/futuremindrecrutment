"""dim_date — generated calendar with weekend + US holiday flags."""

from __future__ import annotations

from datetime import date
from typing import Iterable

import holidays
from sqlmodel import Session, select

from ...constants import WEEKEND_WEEKDAYS
from ...models import DimDate


def calc_date_id(d: date) -> int:
    return d.year * 10000 + d.month * 100 + d.day


class SilverCalendar:
    def __init__(self, session: Session):
        self.session = session

    def ensure_dates(self, dates: Iterable[date]) -> int:
        """Insert dim_date rows for any dates not already present."""
        wanted = sorted({d for d in dates})
        if not wanted:
            return 0

        existing = set(self.session.exec(select(DimDate.date_id)).all())
        us = holidays.US(years=range(wanted[0].year, wanted[-1].year + 1))

        rows: list[DimDate] = []
        for d in wanted:
            did = calc_date_id(d)
            if did in existing:
                continue
            name = us.get(d)
            rows.append(
                DimDate(
                    date_id=did,
                    full_date=d,
                    is_weekend=d.weekday() in WEEKEND_WEEKDAYS,
                    is_holiday=name is not None,
                    holiday_name=name,
                )
            )

        if rows:
            self.session.add_all(rows)
            self.session.flush()
        return len(rows)
