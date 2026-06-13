"""Fact builders — daily revenue (rebuild) and rating snapshots."""

from __future__ import annotations

import pandas as pd

from ..constants import IMDB_SOURCE, UNKNOWN_ID
from ..models.base import utcnow
from ..repositories import FactRepository, MovieRepository, ReferenceRepository


def build_daily_revenue(
    facts: FactRepository,
    movies: MovieRepository,
    reference: ReferenceRepository,
) -> int:
    """Rebuild fact_daily_revenue from bronze: resolve movie/date/distributor, aggregate to grain."""
    rows = facts.read_revenue_grain()
    df = pd.DataFrame(rows, columns=["title", "event_date", "revenue", "theaters", "distributor"])
    if df.empty:
        return 0

    movie_ids = movies.title_to_id()
    dist_ids = reference.distributor_map()

    df["movie_id"] = df["title"].map(movie_ids)
    df = df.dropna(subset=["movie_id"])
    df["movie_id"] = df["movie_id"].astype(int)
    df["distributor_id"] = df["distributor"].map(dist_ids).fillna(UNKNOWN_ID).astype(int)

    event = pd.to_datetime(df["event_date"])
    df["date_id"] = (event.dt.year * 10000 + event.dt.month * 100 + event.dt.day).astype(int)

    agg = df.groupby(["date_id", "movie_id"], as_index=False).agg(
        revenue=("revenue", "sum"),
        theaters=("theaters", "max"),
        distributor_id=("distributor_id", "first"),
    )
    agg["revenue"] = agg["revenue"].astype("Int64")
    agg["theaters"] = agg["theaters"].astype("Int64")
    agg["load_timestamp"] = utcnow()

    facts.replace_daily_revenue(agg)
    return len(agg)


def write_rating_snapshots(
    items, source_ids: dict[str, int], snapshot_date_id: int, facts: FactRepository
) -> int:
    """Write one rating snapshot per (movie, source) for snapshot_date_id (idempotent for the day).

    `items` is an iterable of (movie_id, ParsedMovie). votes attach to the IMDb row only.
    """
    facts.delete_rating_snapshots(snapshot_date_id)

    count = 0
    for movie_id, parsed in items:
        for rating in parsed.ratings:
            source_id = source_ids.get(rating.source_name)
            if source_id is None:
                continue
            facts.add_rating(
                movie_id=movie_id,
                source_id=source_id,
                snapshot_date_id=snapshot_date_id,
                rating_value_native=rating.value_native,
                votes=parsed.votes if rating.source_name == IMDB_SOURCE else None,
            )
            count += 1
    return count
