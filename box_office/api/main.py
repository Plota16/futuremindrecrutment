"""FastAPI app — endpoints only; service layer wired in later."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import text

from .. import config
from ..db import engine, init_db
from .schemas import HealthStatus, LoadSummary, RefreshScope, RefreshSummary


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()  # create schema on startup (idempotent)
    yield


app = FastAPI(title="Box Office Warehouse API", version="0.1.0", lifespan=lifespan)

_NOT_IMPLEMENTED = "service layer not implemented yet"


@app.post("/load/revenues", response_model=LoadSummary, tags=["load"])
def load_revenues(
    file: UploadFile = File(..., description="revenues_per_day.csv"),
    enrich: bool = Form(True, description="call OMDb for movies not yet in the DB"),
    omdb_limit: Optional[int] = Form(None, description="cap on OMDb calls this run"),
) -> LoadSummary:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _NOT_IMPLEMENTED)


@app.post("/load/revenues/demo", response_model=LoadSummary, tags=["load"])
def load_revenues_demo(
    enrich: bool = Query(True),
    omdb_limit: Optional[int] = Query(None),
) -> LoadSummary:
    """Load the bundled CSV (config.CSV_PATH) — no file upload needed."""
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _NOT_IMPLEMENTED)


@app.post("/refresh/movies", response_model=RefreshSummary, tags=["refresh"])
def refresh_movies(
    scope: RefreshScope = Query(RefreshScope.stale),
    stale_days: int = Query(7, ge=0, description="re-fetch movies last refreshed earlier than this"),
    movie_ids: list[int] = Query(default=[], description="used when scope=ids"),
    omdb_limit: Optional[int] = Query(None),
) -> RefreshSummary:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _NOT_IMPLEMENTED)


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
        omdb_key_present=bool(config.OMDB_API_KEY),
    )
