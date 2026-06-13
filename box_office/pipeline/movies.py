"""dim_movie (Type 1, keyed by title) + genre/person bridges."""

from __future__ import annotations

from ..models import DimMovie
from ..models.base import utcnow
from ..models.omdb import ParsedMovie
from ..repositories import MovieRepository


def ensure_movies(titles, repo: MovieRepository) -> dict[str, int]:
    """Ensure a dim_movie row per title; returns title->id."""
    existing = repo.title_to_id()
    new = [DimMovie(title=t) for t in sorted({x for x in titles if x}) if
           t not in existing]
    if new:
        repo.add_all(new)
        for movie in new:
            existing[movie.title] = movie.movie_id
    return existing


def upsert_movie(
        parsed: ParsedMovie,
        repo: MovieRepository,
        genre_ids: dict[str, int],
        person_ids: dict[str, int],
) -> int:
    """Upsert the movie by title; rebuild bridges. Returns movie_id."""
    movie = repo.get_by_title(parsed.title)
    if movie is None:
        movie = DimMovie(title=parsed.title)
        repo.add(movie)

    movie.released_date = parsed.released_date
    movie.runtime_min = parsed.runtime_min
    movie.plot = parsed.plot
    movie.language = parsed.language
    movie.country = parsed.country
    movie.load_timestamp = utcnow()
    repo.flush()  # assign movie_id

    _rebuild_bridges(repo, movie.movie_id, parsed, genre_ids, person_ids)
    return movie.movie_id


def _rebuild_bridges(repo: MovieRepository, movie_id, parsed, genre_ids,
                     person_ids) -> None:
    repo.delete_bridges(movie_id)

    for name in dict.fromkeys(parsed.genres):
        genre_id = genre_ids.get(name)
        if genre_id is not None:
            repo.add_genre_bridge(movie_id, genre_id)

    seen = set()
    for name, role in parsed.persons:
        person_id = person_ids.get(name)
        if person_id is None or (person_id, role) in seen:
            continue
        seen.add((person_id, role))
        repo.add_person_bridge(movie_id, person_id, role)
