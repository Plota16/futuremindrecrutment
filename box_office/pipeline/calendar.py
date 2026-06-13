"""dim_date — generated calendar with weekend + US holiday flags."""

from __future__ import annotations

from datetime import date
from typing import Iterable

import holidays
import pandas as pd
from sqlmodel import Session

from ..models import DimDate
from ..repositories import DateRepository


def date_id(d: date) -> int:
    return d.year * 10000 + d.month * 100 + d.day


def ensure_dates(dates: Iterable[date], session: Session) -> int:
    """Insert dim_date rows for any of the given dates not already present."""
    wanted = sorted({d for d in dates})
    if not wanted:
        return 0

    repo = DateRepository(session)
    existing = repo.existing_ids()
    us = holidays.US(years=range(wanted[0].year, wanted[-1].year + 1))

    rows: list[DimDate] = []
    for d in wanted:
        did = date_id(d)
        if did in existing:
            continue
        name = us.get(d)
        rows.append(
            DimDate(
                date_id=did,
                full_date=d,
                is_weekend=d.weekday() >= 5,
                is_holiday=name is not None,
                holiday_name=name,
            )
        )

    repo.add_all(rows)
    return len(rows)


def ensure_date_range(start: date, end: date, session: Session) -> int:
    """Convenience: ensure every day in [start, end]."""
    return ensure_dates(pd.date_range(start, end, freq="D").date, session)
