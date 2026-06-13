"""Reference dimensions — orchestration over ReferenceRepository.

Data access lives in `repositories.reference`; these are the pipeline-facing
entry points. `UNKNOWN_ID` is re-exported for callers that resolve the
conventional Unknown member.
"""

from __future__ import annotations

from typing import Iterable

from sqlmodel import Session

from ..repositories import ReferenceRepository
from ..repositories.reference import UNKNOWN_ID  # re-exported

__all__ = [
    "UNKNOWN_ID",
    "upsert_distributors",
    "upsert_genres",
    "upsert_persons",
    "seed_rating_sources",
    "ensure_unknown_members",
]


def upsert_distributors(names: Iterable[str], session: Session) -> dict[str, int]:
    return ReferenceRepository(session).upsert_distributors(names)


def upsert_genres(names: Iterable[str], session: Session) -> dict[str, int]:
    return ReferenceRepository(session).upsert_genres(names)


def upsert_persons(names: Iterable[str], session: Session) -> dict[str, int]:
    return ReferenceRepository(session).upsert_persons(names)


def seed_rating_sources(session: Session) -> dict[str, int]:
    return ReferenceRepository(session).seed_rating_sources()


def ensure_unknown_members(session: Session) -> None:
    ReferenceRepository(session).ensure_unknown_members()
