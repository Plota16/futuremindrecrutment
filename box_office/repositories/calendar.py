"""DateRepository — data access for dim_date."""

from __future__ import annotations

from sqlmodel import Session, select

from ..models import DimDate


class DateRepository:
    def __init__(self, session: Session):
        self.session = session

    def existing_ids(self) -> set[int]:
        return set(self.session.exec(select(DimDate.date_id)).all())

    def add_all(self, rows: list[DimDate]) -> None:
        if rows:
            self.session.add_all(rows)
            self.session.flush()
