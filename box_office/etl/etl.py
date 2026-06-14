"""BoxOfficeETL — orchestrates the bronze and silver stages."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from sqlmodel import Session, select

from ..clients import OmdbClient
from ..db import init_db, engine
from ..helpers.parsing import parse_omdb
from ..models import DimMovie, FactMovieRating
from ..models.omdb import OmdbFetchStats
from ..models.results import LoadResult, BronzeResult, SilverCoreResult, \
    SilverEnrichmentResult, SilverResult, RefreshResult
from ..warehouse.silver.calendar import SilverCalendar, calc_date_id
from ..warehouse.silver.facts import SilverFacts
from ..warehouse.silver.movies import SilverMovies
from ..warehouse.bronze.omdb import BronzeOmdb
from ..warehouse.silver.reference import SilverReference
from ..warehouse.bronze.revenue import BronzeRevenue


logger = logging.getLogger(__name__)


def bootstrap() -> None:
    """Create the schema and seed static reference data (on startup)."""
    init_db()
    with Session(engine) as session:
        ref = SilverReference(session)
        ref.seed_rating_sources()
        ref.ensure_unknown_members()
        session.commit()


class BoxOfficeETL:
    def __init__(self, session: Session,
                 omdb_client: Optional[OmdbClient] = None):
        self.session = session
        self.calendar = SilverCalendar(session)
        self.revenue = BronzeRevenue(session)
        self.omdb = BronzeOmdb(session, client=omdb_client)
        self.movies = SilverMovies(session)
        self.facts = SilverFacts(session)
        self.reference = SilverReference(session)

    def run(
            self,
            csv_path: str | Path,
            omdb_limit: Optional[int] = None,
            skip_existing: bool = True,
    ) -> LoadResult:
        """Full load: bronze then silver."""
        bronze = self.etl_bronze(csv_path,
                                 omdb_limit=omdb_limit,
                                 skip_existing=skip_existing)
        silver = self.etl_silver()
        return LoadResult(bronze, silver)

    # Phase 1: bronze landing (CSV)

    def etl_bronze_csv(self, csv_path: str | Path) -> int:
        """Land the CSV 1:1 into bronze. Fast, deterministic, no API."""
        logger.info("bronze csv: start")
        rows = self.revenue.load_csv(csv_path)
        self.session.commit()
        logger.info("bronze csv: done (rows=%d)", rows)
        return rows

    # Phase 2: enrichment cache (OMDb)

    def etl_bronze_omdb(self, omdb_limit: Optional[int] = None,
                        force: bool = False) -> OmdbFetchStats:
        """Fill the OMDb bronze cache, top earners first. Resumable."""
        logger.info("bronze omdb: start")
        stats = self.omdb.fetch(self.revenue.titles_by_revenue(),
                                limit=omdb_limit,
                                force=force)
        self.session.commit()
        logger.info("bronze omdb: done (calls=%d, found=%d)", stats.calls,
                    stats.found)
        return stats

    def etl_bronze(
            self,
            csv_path: str | Path,
            omdb_limit: Optional[int] = None,
            skip_existing: bool = True,
    ) -> BronzeResult:
        rows = self.etl_bronze_csv(csv_path)
        stats = self.etl_bronze_omdb(omdb_limit=omdb_limit,
                                     force=not skip_existing)
        return BronzeResult(rows, stats.requested, stats.calls, stats.found,
                            stats.not_found)

    # Phase 3: silver

    def etl_silver_core(self) -> SilverCoreResult:
        """Silver from the CSV bronze: dates, distributors, movies, facts.

        Independent of the API — runs after every CSV ingest so the ranking
        dashboard is live immediately. Movies are created as inferred members
        (natural key only); API attributes backfill later in enrichment.
        """
        logger.info("silver core: start")
        today = date.today()
        new_dates = list(self.revenue.distinct_event_dates()) + [today]
        dates_added = self.calendar.ensure_dates(new_dates)

        self.reference.ensure_unknown_members()
        self.reference.upsert_distributors(
            self.revenue.distinct_distributors()
        )
        movie_ids = self.movies.ensure(self.revenue.distinct_titles())
        distr_ids = self.reference.distributor_map()
        revenue_rows = self.facts.build_daily_revenue(movie_ids, distr_ids)

        self.session.commit()
        logger.info("silver core: done (movies=%d, revenue_rows=%d)",
                    len(movie_ids), revenue_rows)
        return SilverCoreResult(dates_added, len(movie_ids), revenue_rows)

    def etl_silver_enrichment(self) -> SilverEnrichmentResult:
        """Silver from the OMDb bronze cache: attributes, bridges, ratings.

        Idempotent rebuild over whatever is cached — only movies whose
        API data is "ready" get enriched; the rest fill in as the cache grows.
        """
        logger.info("silver enrichment: start")
        today = date.today()
        self.calendar.ensure_dates([today])
        source_ids = self.reference.seed_rating_sources()

        parsed = [
            parse_omdb(payload, title)
            for title, payload in self.omdb.found_payloads()
        ]

        # Upsert reference dims once for the whole batch (not per movie):
        # each upsert scans the full dim table, so batching turns 2N scans
        # into 2.
        genre_ids = self.reference.upsert_genres(
            {g for p in parsed for g in p.genres}
        )
        person_ids = self.reference.upsert_persons(
            {n for p in parsed for n in p.get_names()}
        )

        enriched = [
            (self.movies.upsert(p, genre_ids, person_ids), p)
            for p in parsed
        ]

        snapshots = self.facts.write_rating_snapshots(
            enriched, source_ids, calc_date_id(today)
        )
        self.session.commit()
        logger.info(
            "silver enrichment: done (movies_enriched=%d, snapshots=%d)",
            len(enriched), snapshots)
        return SilverEnrichmentResult(len(enriched), snapshots)

    def etl_silver(self) -> SilverResult:
        """Full silver = core then enrichment, from current bronze."""
        core = self.etl_silver_core()
        enr = self.etl_silver_enrichment()
        return SilverResult(core.dates_added, core.movies,
                            core.fact_revenue_rows, enr.rating_snapshots)

    def etl_refresh(
            self,
            scope: str = "stale",
            stale_days: int = 7,
            movie_ids: Optional[list[int]] = None,
            omdb_limit: Optional[int] = None,
    ) -> RefreshResult:
        logger.info("refresh: start (scope=%s)", scope)
        titles = self._titles_to_refresh(scope, stale_days, movie_ids)
        stats = self.omdb.fetch(titles, limit=omdb_limit, force=True)
        self.session.commit()
        silver = self.etl_silver()
        logger.info("refresh: done (movies_checked=%d)", len(titles))
        return RefreshResult(len(titles), stats.calls, stats.found,
                             silver.rating_snapshots, silver.fact_revenue_rows)

    def _titles_to_refresh(self, scope, stale_days, movie_ids) -> list[str]:
        session = self.session
        if scope == "ids":
            ids = set(movie_ids or [])
            return [m.title for m in session.exec(
                select(DimMovie).where(DimMovie.movie_id.in_(ids))).all()]
        if scope == "all":
            return [m.title for m in session.exec(select(DimMovie)).all()]

        cutoff = calc_date_id(date.today() - timedelta(days=stale_days))
        latest: dict[int, int] = {}
        for movie_id, snap in session.exec(
                select(FactMovieRating.movie_id,
                       FactMovieRating.snapshot_date_id)
        ).all():
            latest[movie_id] = max(latest.get(movie_id, 0), snap)
        return [m.title for m in session.exec(select(DimMovie)).all() if
                latest.get(m.movie_id, 0) < cutoff]
