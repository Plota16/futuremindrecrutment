from __future__ import annotations

from sqlmodel import Field

from .base import DwhTable


class BridgeMovieGenre(DwhTable, table=True):
    __tablename__ = "bridge_movie_genre"

    movie_id: int = Field(primary_key=True, index=True)
    genre_id: int = Field(primary_key=True, foreign_key="dim_genre.genre_id")


class BridgeMoviePerson(DwhTable, table=True):
    __tablename__ = "bridge_movie_person"

    movie_id: int = Field(primary_key=True, index=True)
    person_id: int = Field(primary_key=True,
                           foreign_key="dim_person.person_id")
    credit_role: str = Field(primary_key=True)  # ACTOR | DIRECTOR | WRITER
