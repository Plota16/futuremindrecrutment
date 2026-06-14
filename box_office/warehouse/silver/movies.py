"""dim_movie (Type 1, keyed by title) + genre/person bridges."""

from __future__ import annotations

from sqlalchemy import delete
from sqlmodel import Session, select

from ...models import (
    BridgeMovieCountry,
    BridgeMovieGenre,
    BridgeMovieLanguage,
    BridgeMoviePerson,
    DimMovie,
)
from ...models.base import utcnow
from ...models.omdb import ParsedMovie


class SilverMovies:
    def __init__(self, session: Session):
        self.session = session

    def title_to_id(self) -> dict[str, int]:
        rows = self.session.exec(select(DimMovie)).all()
        return {m.title: m.movie_id for m in rows}

    def all_titles(self) -> list[str]:
        return [m.title for m in self.session.exec(select(DimMovie)).all()]

    def titles_by_ids(self, ids: set[int]) -> list[str]:
        if not ids:
            return []
        return [
            m.title for m in self.session.exec(
                select(DimMovie).where(DimMovie.movie_id.in_(ids))
            ).all()
        ]

    def ensure(self, titles) -> dict[str, int]:
        """Ensure a dim_movie row per title; returns title->id."""
        existing = self.title_to_id()
        new = [
            DimMovie(title=t)
            for t in sorted({x for x in titles if x})
            if t not in existing
        ]
        if new:
            self.session.add_all(new)
            self.session.flush()
            for movie in new:
                existing[movie.title] = movie.movie_id
        return existing

    def upsert(
        self,
        parsed: ParsedMovie,
        genre_ids: dict[str, int],
        person_ids: dict[str, int],
        language_ids: dict[str, int],
        country_ids: dict[str, int],
    ) -> int:
        """Upsert the movie by title; rebuild all bridges. Returns movie_id."""
        movie = self.session.exec(
            select(DimMovie).where(DimMovie.title == parsed.title)
        ).first()
        if movie is None:
            movie = DimMovie(title=parsed.title)
            self.session.add(movie)

        movie.released_date = parsed.released_date
        movie.runtime_min = parsed.runtime_min
        movie.plot = parsed.plot
        movie.load_timestamp = utcnow()
        self.session.flush()  # assign movie_id

        self._rebuild_bridges(
            movie.movie_id, parsed, genre_ids, person_ids,
            language_ids, country_ids,
        )
        return movie.movie_id

    def _rebuild_bridges(
        self,
        movie_id: int,
        parsed: ParsedMovie,
        genre_ids: dict[str, int],
        person_ids: dict[str, int],
        language_ids: dict[str, int],
        country_ids: dict[str, int],
    ) -> None:
        for bridge_model in (
            BridgeMovieGenre,
            BridgeMoviePerson,
            BridgeMovieLanguage,
            BridgeMovieCountry,
        ):
            self.session.execute(
                delete(bridge_model).where(bridge_model.movie_id == movie_id)
            )

        for name in dict.fromkeys(parsed.genres):
            genre_id = genre_ids.get(name)
            if genre_id is not None:
                self.session.add(
                    BridgeMovieGenre(movie_id=movie_id, genre_id=genre_id)
                )

        seen: set[tuple[int, str]] = set()
        for name, role in parsed.persons:
            person_id = person_ids.get(name)
            if person_id is None or (person_id, role) in seen:
                continue
            seen.add((person_id, role))
            self.session.add(
                BridgeMoviePerson(
                    movie_id=movie_id,
                    person_id=person_id,
                    credit_role=role,
                )
            )

        for name in dict.fromkeys(parsed.languages):
            language_id = language_ids.get(name)
            if language_id is not None:
                self.session.add(
                    BridgeMovieLanguage(
                        movie_id=movie_id, language_id=language_id
                    )
                )

        for name in dict.fromkeys(parsed.countries):
            country_id = country_ids.get(name)
            if country_id is not None:
                self.session.add(
                    BridgeMovieCountry(
                        movie_id=movie_id, country_id=country_id
                    )
                )
