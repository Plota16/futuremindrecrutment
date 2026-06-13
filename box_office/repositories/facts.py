"""FactRepository — data access for the fact tables."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import delete
from sqlmodel import Session, select

from ..models import BronzeRevenueCsv, FactDailyRevenue, FactMovieRating


class FactRepository:
    def __init__(self, session: Session):
        self.session = session

    def read_revenue_grain(self):
        """Raw revenue rows from bronze, at the grain needed to build fact_daily_revenue."""
        return self.session.exec(
            select(
                BronzeRevenueCsv.title,
                BronzeRevenueCsv.event_date,
                BronzeRevenueCsv.revenue,
                BronzeRevenueCsv.theaters,
                BronzeRevenueCsv.distributor,
            )
        ).all()

    def replace_daily_revenue(self, df: pd.DataFrame) -> None:
        self.session.execute(delete(FactDailyRevenue))
        df.to_sql(FactDailyRevenue.__tablename__, self.session.connection(), if_exists="append", index=False)

    def delete_rating_snapshots(self, snapshot_date_id: int) -> None:
        self.session.execute(
            delete(FactMovieRating).where(FactMovieRating.snapshot_date_id == snapshot_date_id)
        )

    def add_rating(
        self,
        movie_id: int,
        source_id: int,
        snapshot_date_id: int,
        rating_value_native: float,
        votes: int | None,
    ) -> None:
        self.session.add(
            FactMovieRating(
                movie_id=movie_id,
                source_id=source_id,
                snapshot_date_id=snapshot_date_id,
                rating_value_native=rating_value_native,
                votes=votes,
            )
        )
