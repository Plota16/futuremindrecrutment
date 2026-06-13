"""OMDb API client — title lookup, returns the raw payload for bronze."""

from __future__ import annotations

from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .. import config
from ..constants import OMDB_POOL_SIZE, OMDB_RETRY_BACKOFF, \
    OMDB_RETRY_STATUSES, OMDB_RETRY_TOTAL
from ..models.omdb import OmdbResult

_RETRY = Retry(
    total=OMDB_RETRY_TOTAL,
    backoff_factor=OMDB_RETRY_BACKOFF,
    status_forcelist=OMDB_RETRY_STATUSES,
    allowed_methods=("GET",),
)


def _build_session() -> requests.Session:
    session = requests.Session()
    adapter = HTTPAdapter(pool_connections=OMDB_POOL_SIZE,
                          pool_maxsize=OMDB_POOL_SIZE, max_retries=_RETRY)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class OmdbClient:
    def __init__(
            self,
            api_key: str = "",
            base_url: Optional[str] = None,
            timeout: float = 10.0,
            session: Optional[requests.Session] = None,
    ):
        settings = config.get_settings()
        self.api_key = api_key or settings.omdb_api_key
        self.base_url = base_url or settings.omdb_base_url
        self.timeout = timeout
        self.session = session or _build_session()

    def fetch_by_title(self, title: str) -> OmdbResult:
        if not self.api_key:
            raise RuntimeError("OMDB_API_KEY is not set")
        params = {"apikey": self.api_key, "t": title}
        resp = self.session.get(self.base_url, params=params,
                                timeout=self.timeout)
        resp.raise_for_status()
        found = resp.json().get("Response") == "True"
        return OmdbResult(found=found, raw_json=resp.text)
