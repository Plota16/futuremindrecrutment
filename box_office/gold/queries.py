"""GoldQueries — read-only serving queries for the dashboards (gold layer).

Computation stays in SQL (aggregation, joins, window functions); pandas is
used only as the transport/render format the Streamlit charts expect. Each
ranking returns at most TOP_N rows.
"""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text
from sqlmodel import Session

from box_office.constants import (
    IMDB_SOURCE,
    METACRITIC_SOURCE,
    ROTTEN_TOMATOES_SOURCE,
    TOP_N,
)


class GoldQueries:
    def __init__(self, session: Session):
        self.session = session

    def _df(self, sql: str, params: dict | None = None) -> pd.DataFrame:
        conn = self.session.connection()
        return pd.read_sql_query(text(sql), conn, params=params or {})

    def available_years(self) -> list[int]:
        """Distinct years in the revenue fact, newest first (year picker)."""
        df = self._df(
            """
            SELECT DISTINCT date_id / 10000 AS year
            FROM fact_daily_revenue
            ORDER BY year DESC
            """
        )
        return [int(y) for y in df["year"].tolist()]

    def top_movies_by_year(
        self, year: int, limit: int = TOP_N
    ) -> pd.DataFrame:
        """Top earning movies for a year (date_id is YYYYMMDD)."""
        return self._df(
            """
            SELECT m.title AS title, SUM(f.revenue) AS box_office
            FROM fact_daily_revenue f
            JOIN dim_movie m ON m.movie_id = f.movie_id
            WHERE f.date_id / 10000 = :year
            GROUP BY m.movie_id, m.title
            ORDER BY box_office DESC
            LIMIT :limit
            """,
            {"year": year, "limit": limit},
        )

    def top_movies_all_time(self, limit: int = TOP_N) -> pd.DataFrame:
        """Top earning movies across every year (no year filter)."""
        return self._df(
            """
            SELECT m.title AS title, SUM(f.revenue) AS box_office
            FROM fact_daily_revenue f
            JOIN dim_movie m ON m.movie_id = f.movie_id
            GROUP BY m.movie_id, m.title
            ORDER BY box_office DESC
            LIMIT :limit
            """,
            {"limit": limit},
        )

    def top_rated_movies(self, limit: int = TOP_N) -> pd.DataFrame:
        """Top movies by mean normalized rating, plus native per-source scores.

        Each source's native value is normalized to 0-100
        (value / scale_max * 100) so the three scales (IMDb /10,
        RT/Metacritic /100) are comparable; the mean of those drives the
        ranking. The per-source columns show the raw native scores.
        ROW_NUMBER keeps only each movie's latest snapshot per source.
        """
        return self._df(
            """
            WITH latest AS (
                SELECT r.movie_id,
                       s.source_name AS source_name,
                       r.rating_value_native AS native,
                       r.rating_value_native * 100.0 / s.scale_max
                           AS normalized,
                       ROW_NUMBER() OVER (
                           PARTITION BY r.movie_id, r.source_id
                           ORDER BY r.snapshot_date_id DESC
                       ) AS rn
                FROM fact_movie_rating r
                JOIN dim_rating_source s ON s.source_id = r.source_id
            )
            SELECT m.title AS title,
                   ROUND(AVG(l.normalized), 1) AS avg_score,
                   MAX(CASE WHEN l.source_name = :imdb
                            THEN l.native END) AS imdb,
                   MAX(CASE WHEN l.source_name = :meta
                            THEN l.native END) AS metacritic,
                   MAX(CASE WHEN l.source_name = :rt
                            THEN l.native END) AS rotten_tomatoes
            FROM latest l
            JOIN dim_movie m ON m.movie_id = l.movie_id
            WHERE l.rn = 1
            GROUP BY l.movie_id, m.title
            ORDER BY avg_score DESC
            LIMIT :limit
            """,
            {
                "imdb": IMDB_SOURCE,
                "meta": METACRITIC_SOURCE,
                "rt": ROTTEN_TOMATOES_SOURCE,
                "limit": limit,
            },
        )

    def top_by_role(self, role: str, limit: int = TOP_N) -> pd.DataFrame:
        """Top people by box office of their films, for one credit role.

        Each credited person is attributed the full box office of every
        film they worked on (standard, non-split attribution).
        """
        return self._df(
            """
            SELECT p.person_name AS name, SUM(f.revenue) AS box_office
            FROM fact_daily_revenue f
            JOIN bridge_movie_person b
              ON b.movie_id = f.movie_id AND b.credit_role = :role
            JOIN dim_person p ON p.person_id = b.person_id
            GROUP BY p.person_id, p.person_name
            ORDER BY box_office DESC
            LIMIT :limit
            """,
            {"role": role, "limit": limit},
        )

    def top_holidays(self, limit: int = TOP_N) -> pd.DataFrame:
        """Most profitable holidays by box office (across years)."""
        return self._df(
            """
            SELECT d.holiday_name AS holiday, SUM(f.revenue) AS box_office
            FROM fact_daily_revenue f
            JOIN dim_date d ON d.date_id = f.date_id
            WHERE d.is_holiday = 1 AND d.holiday_name IS NOT NULL
            GROUP BY d.holiday_name
            ORDER BY box_office DESC
            LIMIT :limit
            """,
            {"limit": limit},
        )

    def revenue_by_daytype(self) -> pd.DataFrame:
        """Box office split into weekend/holiday vs weekday (pie chart)."""
        return self._df(
            """
            SELECT CASE WHEN d.is_weekend = 1 OR d.is_holiday = 1
                        THEN 'Weekend/Holiday' ELSE 'Weekday' END AS day_type,
                   SUM(f.revenue) AS box_office
            FROM fact_daily_revenue f
            JOIN dim_date d ON d.date_id = f.date_id
            GROUP BY day_type
            ORDER BY box_office DESC
            """
        )

    def top_theaters_peak(self, limit: int = TOP_N) -> pd.DataFrame:
        """Films ranked by peak theater count, with the day it occurred.

        ROW_NUMBER picks each film's max-theaters day (ties broken by
        earliest date); the outer query ranks those peaks across films.
        """
        return self._df(
            """
            SELECT title, theaters, peak_date
            FROM (
                SELECT m.title AS title,
                       f.theaters AS theaters,
                       d.full_date AS peak_date,
                       ROW_NUMBER() OVER (
                           PARTITION BY f.movie_id
                           ORDER BY f.theaters DESC, f.date_id ASC
                       ) AS rn
                FROM fact_daily_revenue f
                JOIN dim_movie m ON m.movie_id = f.movie_id
                JOIN dim_date d ON d.date_id = f.date_id
                WHERE f.theaters IS NOT NULL
            ) ranked
            WHERE rn = 1
            ORDER BY theaters DESC
            LIMIT :limit
            """,
            {"limit": limit},
        )
