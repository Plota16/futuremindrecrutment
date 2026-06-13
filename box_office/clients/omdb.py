"""OMDb API client — title lookup, returns the raw payload for bronze."""

from __future__ import annotations

from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .. import config
from ..models.omdb import OmdbResult

# Pool generously so concurrent workers don't queue on connections.
_POOL_SIZE = 32
_RETRY = Retry(
    total=3,
    backoff_factor=0.5,                       # 0.5s, 1s, 2s between retries
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=("GET",),
)


def _build_session() -> requests.Session:
    session = requests.Session()
    adapter = HTTPAdapter(pool_connections=_POOL_SIZE, pool_maxsize=_POOL_SIZE, max_retries=_RETRY)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class OmdbClient:
    def __init__(
        self,
        api_key: str = "",
        base_url: str = config.settings.omdb_base_url,
        timeout: float = 10.0,
        session: Optional[requests.Session] = None,
    ):
        self.api_key = api_key or config.settings.omdb_api_key
        self.base_url = base_url
        self.timeout = timeout
        self.session = session or _build_session()

    def fetch_by_title(self, title: str, year: Optional[int] = None) -> OmdbResult:
        if not self.api_key:
            raise RuntimeError("OMDB_API_KEY is not set")
        params = {"apikey": self.api_key, "t": title}
        if year:
            params["y"] = year
        resp = self.session.get(self.base_url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        payload = resp.json()
        return OmdbResult(
            title_queried=title,
            found=payload.get("Response") == "True",
            raw_json=resp.text,
            payload=payload,
        )
