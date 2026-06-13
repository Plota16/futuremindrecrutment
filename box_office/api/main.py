"""FastAPI app — endpoints wired to BoxOfficeETL"""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
import time
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile, \
    status
from sqlalchemy import text
from sqlmodel import Session

from .. import config
from ..db import engine, get_session
from ..logging_config import configure_logging
from ..models.api import (
    CsvLoadSummary,
    HealthStatus,
    LoadSummary,
    OmdbLoadSummary,
    RefreshScope,
    RefreshSummary,
    SilverSummary,
)
from ..pipeline.etl import BoxOfficeETL, bootstrap

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    bootstrap()  # schema + seeds
    yield


app = FastAPI(title="Box Office Warehouse API", version="0.1.0",
              lifespan=lifespan)


@contextmanager
def _csv_source(file: Optional[UploadFile]):
    if file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        try:
            yield tmp_path
        finally:
            os.unlink(tmp_path)
    else:
        if not Path(config.CSV_PATH).exists():
            raise HTTPException(status.HTTP_404_NOT_FOUND,
                                f"bundled CSV not found at {config.CSV_PATH}")
        yield str(config.CSV_PATH)


@app.post("/load/csv", response_model=CsvLoadSummary, tags=["load"])
def load_csv(
        file: Optional[UploadFile] = File(
            None,
            description="revenues CSV; omit to use the bundled demo file",
        ),
        session: Session = Depends(get_session),
) -> CsvLoadSummary:
    """Phase 1 — land the CSV into bronze. Fast, no API."""
    logger.info("POST /load/csv: start (file=%s)",
                file.filename if file else "<bundled>")
    started = time.perf_counter()
    with _csv_source(file) as csv_path:
        rows = BoxOfficeETL(session).etl_bronze_csv(csv_path)
    summary = CsvLoadSummary(rows_read=rows, duration_ms=int(
        (time.perf_counter() - started) * 1000))
    logger.info("POST /load/csv: done in %dms", summary.duration_ms)
    return summary


@app.post("/load/omdb", response_model=OmdbLoadSummary, tags=["load"])
def load_omdb(
        omdb_limit: Optional[int] = Query(
            None,
            description="max API calls this run (daily-quota friendly)",
        ),
        force: bool = Query(
            False, description="re-fetch already-cached titles"
        ),
        session: Session = Depends(get_session),
) -> OmdbLoadSummary:
    """Phase 2 — fill the OMDb bronze cache (top earners first)."""
    logger.info("POST /load/omdb: start (limit=%s, force=%s)", omdb_limit,
                force)
    started = time.perf_counter()
    stats = BoxOfficeETL(session).etl_bronze_omdb(omdb_limit=omdb_limit,
                                                  force=force)
    summary = OmdbLoadSummary(
        omdb_requested=stats.requested,
        omdb_skipped_cached=stats.skipped_cached,
        omdb_calls=stats.calls,
        omdb_found=stats.found,
        omdb_not_found=stats.not_found,
        duration_ms=int((time.perf_counter() - started) * 1000),
    )
    logger.info("POST /load/omdb: done in %dms", summary.duration_ms)
    return summary


@app.post("/load/silver", response_model=SilverSummary, tags=["load"])
def load_silver(session: Session = Depends(get_session)) -> SilverSummary:
    """Phase 3 — rebuild silver from the current bronze state."""
    logger.info("POST /load/silver: start")
    started = time.perf_counter()
    etl = BoxOfficeETL(session)
    core = etl.etl_silver_core()
    enr = etl.etl_silver_enrichment()
    summary = SilverSummary(
        dates_added=core.dates_added,
        movies=core.movies,
        fact_revenue_rows=core.fact_revenue_rows,
        movies_enriched=enr.movies_enriched,
        rating_snapshots=enr.rating_snapshots,
        duration_ms=int((time.perf_counter() - started) * 1000),
    )
    logger.info("POST /load/silver: done in %dms", summary.duration_ms)
    return summary


@app.post("/load/all", response_model=LoadSummary, tags=["load"])
def load_all(
        file: Optional[UploadFile] = File(
            None,
            description="revenues CSV; omit to use the bundled demo file",
        ),
        omdb_limit: Optional[int] = Query(
            None,
            description="max API calls (omit = no limit, ignores quota)",
        ),
        session: Session = Depends(get_session),
) -> LoadSummary:
    """Run all phases end to end (CSV + OMDb + silver). For dev/demo."""
    logger.info("POST /load/all: start (file=%s, limit=%s)",
                file.filename if file else "<bundled>", omdb_limit)
    started = time.perf_counter()
    with _csv_source(file) as csv_path:
        result = BoxOfficeETL(session).run(csv_path, omdb_limit=omdb_limit)
    b, s = result.bronze, result.silver
    summary = LoadSummary(
        rows_read=b.rows_read,
        omdb_calls=b.omdb_calls,
        omdb_found=b.omdb_found,
        omdb_not_found=b.omdb_not_found,
        dates_added=s.dates_added,
        movies=s.movies,
        fact_revenue_rows=s.fact_revenue_rows,
        rating_snapshots=s.rating_snapshots,
        duration_ms=int((time.perf_counter() - started) * 1000),
    )
    logger.info("POST /load/all: done in %dms", summary.duration_ms)
    return summary


@app.post("/refresh/movies", response_model=RefreshSummary, tags=["refresh"])
def refresh_movies(
        scope: RefreshScope = Query(RefreshScope.stale),
        stale_days: int = Query(7, ge=0),
        movie_ids: list[int] = Query(default=[]),
        omdb_limit: Optional[int] = Query(None),
        session: Session = Depends(get_session),
) -> RefreshSummary:
    logger.info("POST /refresh/movies: start (scope=%s)", scope.value)
    started = time.perf_counter()
    r = BoxOfficeETL(session).etl_refresh(
        scope=scope.value, stale_days=stale_days, movie_ids=movie_ids or None,
        omdb_limit=omdb_limit
    )
    logger.info("POST /refresh/movies: done in %dms",
                int((time.perf_counter() - started) * 1000))
    return RefreshSummary(
        movies_checked=r.movies_checked,
        omdb_calls=r.omdb_calls,
        omdb_found=r.omdb_found,
        rating_snapshots=r.rating_snapshots,
        fact_revenue_rows=r.fact_revenue_rows,
        duration_ms=int((time.perf_counter() - started) * 1000),
    )


@app.get("/health", response_model=HealthStatus, tags=["ops"])
def health() -> HealthStatus:
    db_ok = True
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    return HealthStatus(
        status="ok" if db_ok else "degraded",
        db_ok=db_ok,
        omdb_key_present=bool(config.get_settings().omdb_api_key),
    )
