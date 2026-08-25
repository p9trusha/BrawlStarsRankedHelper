from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_TIMEOUT = 30
HEADERS = {"User-Agent": "Mozilla/5.0 (BrawlStarsHelper/1.0)"}

_retry = Retry(
    total=2,
    backoff_factor=0.5,
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=("GET", "HEAD"),
)

session = requests.Session()
session.headers.update(HEADERS)
adapter = HTTPAdapter(max_retries=_retry)
session.mount("https://", adapter)
session.mount("http://", adapter)


def get_json(
    url: str, headers: dict[str, str] | None = None, timeout: int = DEFAULT_TIMEOUT
) -> Any:
    resp = session.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def head_ok_image(url: str, timeout: int = 10) -> bool:
    try:
        resp = session.head(url, timeout=timeout)
    except requests.RequestException:
        return False
    return resp.status_code == 200 and "image" in resp.headers.get("content-type", "")
