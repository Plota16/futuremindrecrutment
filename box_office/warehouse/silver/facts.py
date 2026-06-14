"""Fact builders — daily revenue (rebuild) and rating snapshots."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import delete
from sqlmodel import Session, select

from ...constants import IMDB_SOURCE, UNKNOWN_ID
from ...models import BronzeRevenueCsv, FactDailyRevenue, FactMovieRating
from ...models.base import utcnow


class SilverFacts:
    def __init__(self, session: Session):
        self.session = session

    def build_daily_revenue(
        self, movie_ids: dict[str, int], dist_ids: dict[str, int]
    ) -> int:
        """Rebuild fact_daily_revenue from bronze, aggregated to grain.

        Resolution maps (title->movie_id, distributor->id) are passed in so
        this owns no cross-table reads beyond the bronze source.
        """
        rows = self.session.exec(
            select(
                BronzeRevenueCsv.title,
                BronzeRevenueCsv.event_date,
                BronzeRevenueCsv.revenue,
                BronzeRevenueCsv.theaters,
                BronzeRevenueCsv.distributor,
            )
        ).all()
        df = pd.DataFrame(
            rows,
            columns=["title", "event_date", "revenue", "theaters",
                     "distributor"],
        )
        if df.empty:
            return 0

        df["movie_id"] = df["title"].map(movie_ids)
        df = df.dropna(subset=["movie_id"])
        df["movie_id"] = df["movie_id"].astype(int)
        df["distributor_id"] = (
            df["distributor"].map(dist_ids).fillna(UNKNOWN_ID).astype(int)
        )

        event = pd.to_datetime(df["event_date"])
        df["date_id"] = (
            event.dt.year * 10000 + event.dt.month * 100 + event.dt.day
        ).astype(int)

        agg = df.groupby(["date_id", "movie_id"], as_index=False).agg(
            revenue=("revenue", "sum"),
            theaters=("theaters", "max"),
            distributor_id=("distributor_id", "first"),
        )
        agg["revenue"] = agg["revenue"].astype("Int64")
        agg["theaters"] = agg["theaters"].astype("Int64")
        agg["load_timestamp"] = utcnow()

        self.session.execute(delete(FactDailyRevenue))
        agg.to_sql(
            FactDailyRevenue.__tablename__,
            self.session.connection(),
            if_exists="append",
            index=False,
        )
        return len(agg)

    def latest_snapshot_by_movie(self) -> dict[int, int]:
        """Return {movie_id: max snapshot_date_id} for every rated movie."""
        result: dict[int, int] = {}
        for movie_id, snap in self.session.exec(
            select(FactMovieRating.movie_id, FactMovieRating.snapshot_date_id)
        ).all():
            result[movie_id] = max(result.get(movie_id, 0), snap)
        return result

    def write_rating_snapshots(
        self, items, source_ids: dict[str, int], snapshot_date_id: int
    ) -> int:
        """Write one rating snapshot per (movie, source) for the day.

        `items` is an iterable of (movie_id, ParsedMovie); votes are
        IMDb-only.
        """
        self.session.execute(
            delete(FactMovieRating).where(
                FactMovieRating.snapshot_date_id == snapshot_date_id
            )
        )

        count = 0
        for movie_id, parsed in items:
            for rating in parsed.ratings:
                source_id = source_ids.get(rating.source_name)
                if source_id is None:
                    continue
                is_imdb = rating.source_name == IMDB_SOURCE
                self.session.add(
                    FactMovieRating(
                        movie_id=movie_id,
                        source_id=source_id,
                        snapshot_date_id=snapshot_date_id,
                        rating_value_native=rating.value_native,
                        votes=parsed.votes if is_imdb else None,
                    )
                )
                count += 1
        return count
