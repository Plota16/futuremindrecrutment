"""bronze_omdb_raw — OMDb cache + concurrent fetch."""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable, Optional

from sqlmodel import Session, select

from ... import config
from ...clients.omdb import OmdbClient
from ...logging_config import log_progress
from ...models import BronzeOmdbRaw
from ...models.omdb import OmdbFetchStats, OmdbResult

logger = logging.getLogger(__name__)


class BronzeOmdb:
    def __init__(self, session: Session,
                 client: Optional[OmdbClient] = None):
        self.session = session
        self.client = client or OmdbClient()

    def cached_titles(self) -> set[str]:
        return set(
            self.session.exec(
                select(BronzeOmdbRaw.title_queried).distinct()
            ).all()
        )

    def fetch(
        self,
        titles: Iterable[str],
        limit: Optional[int] = None,
        force: bool = False,
        max_workers: Optional[int] = None,
    ) -> OmdbFetchStats:
        """Fetch titles from OMDb, storing raw JSON. Skips cached unless force.

        Network calls run on a bounded thread pool; results are written to
        the session on this (single) thread, since the SQLAlchemy session is
        not thread-safe.
        """
        titles = list(dict.fromkeys(titles))
        requested = len(titles)
        if force:
            pending = list(titles)
        else:
            cached = self.cached_titles()
            pending = [t for t in titles if t not in cached]
        skipped = requested - len(pending)

        if limit is not None:
            pending = pending[:limit]

        total = len(pending)
        if not total:
            return OmdbFetchStats(requested, skipped, 0, 0, 0)

        workers = min(
            max_workers or config.get_settings().omdb_max_workers, total
        )
        logger.info(
            "omdb fetch: start (%d titles, force=%s, workers=%d)",
            total, force, workers,
        )

        found = not_found = 0
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(self._safe_fetch, title): title
                for title in pending
            }
            for i, future in enumerate(as_completed(futures), 1):
                title = futures[future]
                result = future.result()
                if result is None:
                    not_found += 1
                else:
                    self.session.add(
                        BronzeOmdbRaw(
                            title_queried=title,
                            found=result.found,
                            response_json=result.raw_json,
                        )
                    )
                    found += result.found
                    not_found += not result.found
                log_progress(logger, "omdb movies", i, total)

        self.session.flush()
        logger.info("omdb fetch: done (%d calls, %d found)", total, found)
        return OmdbFetchStats(requested, skipped, total, found, not_found)

    def _safe_fetch(self, title: str) -> Optional[OmdbResult]:
        """Fetch one title; swallow transient errors (never abort batch)."""
        try:
            return self.client.fetch_by_title(title)
        except Exception as exc:  # noqa: BLE001 — HTTP errors expected
            logger.warning("omdb fetch failed for %r: %s", title, exc)
            return None

    def found_payloads(self) -> list[tuple[str, dict]]:
        """Latest found payload per title (refresh appends, keep newest)."""
        rows = self.session.exec(
            select(BronzeOmdbRaw.title_queried, BronzeOmdbRaw.response_json)
            .where(BronzeOmdbRaw.found == True)  # noqa: E712
            .order_by(BronzeOmdbRaw.bronze_omdb_id)
        ).all()
        latest = {title: raw for title, raw in rows}
        return [(title, json.loads(raw)) for title, raw in latest.items()]
