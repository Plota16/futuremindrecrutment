from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DwhTable(SQLModel):

    load_timestamp: datetime = Field(default_factory=utcnow, nullable=False)
