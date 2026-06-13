"""dim_date — generated calendar with weekend + US holiday flags."""

from __future__ import annotations

from datetime import date
from typing import Iterable

import holidays

from ..models import DimDate
from ..repositories import DateRepository


def date_id(d: date) -> int:
    return d.year * 10000 + d.month * 100 + d.day


def ensure_dates(dates: Iterable[date], repo: DateRepository) -> int:
    """Insert dim_date rows for any of the given dates not already present."""
    wanted = sorted({d for d in dates})
    if not wanted:
        return 0

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
