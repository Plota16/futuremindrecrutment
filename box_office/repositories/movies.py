"""MovieRepository — data access for dim_movie and its genre/person bridges."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import delete
from sqlmodel import Session, select

from ..models import BridgeMovieGenre, BridgeMoviePerson, DimMovie


class MovieRepository:
    def __init__(self, session: Session):
        self.session = session

    def title_to_id(self) -> dict[str, int]:
        return {m.title: m.movie_id for m in
                self.session.exec(select(DimMovie)).all()}

    def get_by_title(self, title: str) -> Optional[DimMovie]:
        return self.session.exec(
            select(DimMovie).where(DimMovie.title == title)).first()

    def add(self, movie: DimMovie) -> None:
        self.session.add(movie)

    def add_all(self, movies: list[DimMovie]) -> None:
        if movies:
            self.session.add_all(movies)
            self.session.flush()

    def flush(self) -> None:
        self.session.flush()

    def delete_bridges(self, movie_id: int) -> None:
        self.session.execute(delete(BridgeMovieGenre).where(
            BridgeMovieGenre.movie_id == movie_id))
        self.session.execute(delete(BridgeMoviePerson).where(
            BridgeMoviePerson.movie_id == movie_id))

    def add_genre_bridge(self, movie_id: int, genre_id: int) -> None:
        self.session.add(
            BridgeMovieGenre(movie_id=movie_id, genre_id=genre_id))

    def add_person_bridge(self, movie_id: int, person_id: int,
                          credit_role: str) -> None:
        self.session.add(
            BridgeMoviePerson(movie_id=movie_id, person_id=person_id,
                              credit_role=credit_role))
