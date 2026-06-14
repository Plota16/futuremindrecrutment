"""Reference dimensions — distributor / genre / person / rating source.

Owns the static seed config (rating sources, the conventional Unknown
member). No method commits; the orchestrator controls the transaction.
"""

from __future__ import annotations

from typing import Iterable

from sqlmodel import Session, select

from ...constants import RATING_SOURCES, UNKNOWN_ID
from ...models import (
    DimCountry,
    DimDistributor,
    DimGenre,
    DimLanguage,
    DimPerson,
    DimRatingSource,
)


class SilverReference:
    def __init__(self, session: Session):
        self.session = session

    def _upsert(self, model, name_attr, id_attr, names) -> dict[str, int]:
        existing = {
            getattr(r, name_attr): getattr(r, id_attr)
            for r in self.session.exec(select(model)).all()
        }
        new = [
            model(**{name_attr: n})
            for n in sorted({x for x in names if x})
            if n not in existing
        ]
        if new:
            self.session.add_all(new)
            self.session.flush()
            for obj in new:
                existing[getattr(obj, name_attr)] = getattr(obj, id_attr)
        return existing

    def upsert_distributors(self, names: Iterable[str]) -> dict[str, int]:
        return self._upsert(
            DimDistributor, "distributor_name", "distributor_id", names
        )

    def upsert_genres(self, names: Iterable[str]) -> dict[str, int]:
        return self._upsert(DimGenre, "genre_name", "genre_id", names)

    def upsert_persons(self, names: Iterable[str]) -> dict[str, int]:
        return self._upsert(DimPerson, "person_name", "person_id", names)

    def upsert_languages(self, names: Iterable[str]) -> dict[str, int]:
        return self._upsert(DimLanguage, "language_name", "language_id", names)

    def upsert_countries(self, names: Iterable[str]) -> dict[str, int]:
        return self._upsert(DimCountry, "country_name", "country_id", names)

    def seed_rating_sources(self) -> dict[str, int]:
        existing = {
            r.source_name: r.source_id
            for r in self.session.exec(select(DimRatingSource)).all()
        }
        for source_id, name, scale_max, scale_unit in RATING_SOURCES:
            if name not in existing:
                self.session.add(
                    DimRatingSource(
                        source_id=source_id,
                        source_name=name,
                        scale_max=scale_max,
                        scale_unit=scale_unit,
                    )
                )
                existing[name] = source_id
        return existing

    def ensure_unknown_members(self) -> None:
        """Unknown distributor (id 0) so the fact never has a NULL FK."""
        if self.session.get(DimDistributor, UNKNOWN_ID) is None:
            self.session.add(
                DimDistributor(
                    distributor_id=UNKNOWN_ID, distributor_name="Unknown"
                )
            )
            self.session.flush()

    def distributor_map(self) -> dict[str, int]:
        rows = self.session.exec(select(DimDistributor)).all()
        return {d.distributor_name: d.distributor_id for d in rows}
