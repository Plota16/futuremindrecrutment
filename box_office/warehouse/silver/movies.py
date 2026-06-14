"""dim_movie (Type 1, keyed by title) + genre/person bridges."""

from __future__ import annotations

from sqlalchemy import delete
from sqlmodel import Session, select

from ...models import BridgeMovieGenre, BridgeMoviePerson, DimMovie
from ...models.base import utcnow
from ...models.omdb import ParsedMovie


class SilverMovies:
    def __init__(self, session: Session):
        self.session = session

    def title_to_id(self) -> dict[str, int]:
        rows = self.session.exec(select(DimMovie)).all()
        return {m.title: m.movie_id for m in rows}

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
    ) -> int:
        """Upsert the movie by title; rebuild bridges. Returns movie_id."""
        movie = self.session.exec(
            select(DimMovie).where(DimMovie.title == parsed.title)
        ).first()
        if movie is None:
            movie = DimMovie(title=parsed.title)
            self.session.add(movie)

        movie.released_date = parsed.released_date
        movie.runtime_min = parsed.runtime_min
        movie.plot = parsed.plot
        movie.language = parsed.language
        movie.country = parsed.country
        movie.load_timestamp = utcnow()
        self.session.flush()  # assign movie_id

        self._rebuild_bridges(movie.movie_id, parsed, genre_ids, person_ids)
        return movie.movie_id

    def _rebuild_bridges(
        self, movie_id, parsed, genre_ids, person_ids
    ) -> None:
        self.session.execute(
            delete(BridgeMovieGenre).where(
                BridgeMovieGenre.movie_id == movie_id
            )
        )
        self.session.execute(
            delete(BridgeMoviePerson).where(
                BridgeMoviePerson.movie_id == movie_id
            )
        )

        for name in dict.fromkeys(parsed.genres):
            genre_id = genre_ids.get(name)
            if genre_id is not None:
                self.session.add(
                    BridgeMovieGenre(movie_id=movie_id, genre_id=genre_id)
                )

        seen = set()
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
