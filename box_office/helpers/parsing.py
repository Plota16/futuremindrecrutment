"""Pure OMDb JSON → structured DTO. No DB access."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional

from ..constants import CREDIT_ACTOR as ACTOR, CREDIT_DIRECTOR as DIRECTOR, \
    CREDIT_WRITER as WRITER
from ..models.omdb import ParsedMovie, ParsedRating

_NA = {"", "N/A", "NA"}
_PARENS = re.compile(r"\s*\([^)]*\)")


def _clean(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    v = value.strip()
    return None if v in _NA else v


def _released(value: Optional[str]) -> Optional[date]:
    v = _clean(value)
    if not v:
        return None
    try:
        return datetime.strptime(v, "%d %b %Y").date()
    except ValueError:
        return None


def _runtime(value: Optional[str]) -> Optional[int]:
    v = _clean(value)
    if not v:
        return None
    head = v.split()[0].replace(",", "")
    return int(head) if head.isdigit() else None


def _votes(value: Optional[str]) -> Optional[int]:
    v = _clean(value)
    if not v:
        return None
    digits = v.replace(",", "")
    return int(digits) if digits.isdigit() else None


def _names(value: Optional[str]) -> list[str]:
    v = _clean(value)
    if not v:
        return []
    names = []
    for part in v.split(","):
        name = _PARENS.sub("", part).strip()
        if name and name not in _NA:
            names.append(name)
    return names


def _csv_list(value: Optional[str]) -> list[str]:
    """Split a comma-separated OMDb string (genres, languages, countries…)."""
    v = _clean(value)
    if not v:
        return []
    return [item.strip() for item in v.split(",")
            if item.strip() and item.strip() not in _NA]


def _genres(value: Optional[str]) -> list[str]:
    return _csv_list(value)


def _rating_value(value: str) -> float:
    return float(value.split("/")[0].strip().rstrip("%").strip())


def _ratings(items) -> list[ParsedRating]:
    out = []
    for item in items or []:
        source = _clean(item.get("Source"))
        value = item.get("Value")
        if not source or not value:
            continue
        try:
            out.append(ParsedRating(source, _rating_value(value)))
        except ValueError:
            continue
    return out


def parse_omdb(payload: dict, title: str) -> ParsedMovie:
    persons: list[tuple[str, str]] = []
    persons += [(n, DIRECTOR) for n in _names(payload.get("Director"))]
    persons += [(n, WRITER) for n in _names(payload.get("Writer"))]
    persons += [(n, ACTOR) for n in _names(payload.get("Actors"))]
    persons = list(dict.fromkeys(persons))  # dedup (name, role)

    return ParsedMovie(
        title=title,
        released_date=_released(payload.get("Released")),
        runtime_min=_runtime(payload.get("Runtime")),
        plot=_clean(payload.get("Plot")),
        languages=_csv_list(payload.get("Language")),
        countries=_csv_list(payload.get("Country")),
        genres=_genres(payload.get("Genre")),
        persons=persons,
        ratings=_ratings(payload.get("Ratings")),
        votes=_votes(payload.get("imdbVotes")),
    )
