"""Cliente HTTP con retry (misma idea que SportsbookScraperAPI)."""
from __future__ import annotations

import time
from typing import Callable, Optional

import requests
from requests.adapters import HTTPAdapter
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from urllib3.util.retry import Retry


def get_user_agent_rotator():
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    ]
    idx = [0]

    def next_ua() -> str:
        ua = agents[idx[0] % len(agents)]
        idx[0] += 1
        return ua

    return next_ua


_next_ua = get_user_agent_rotator()


def next_user_agent() -> str:
    return _next_ua()


def with_delay(min_seconds: float = 0.5, max_seconds: float = 2.0) -> None:
    time.sleep(min_seconds)


def retry_with_backoff(
    fn: Optional[Callable] = None,
    *,
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
):
    def decorator(func):
        return retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type((ConnectionError, TimeoutError)),
            reraise=True,
        )(func)

    if fn is not None:
        return decorator(fn)
    return decorator


def create_session(
    base_headers: Optional[dict] = None,
    retries: int = 3,
    backoff_factor: float = 0.5,
) -> requests.Session:
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
    session.mount("http://", HTTPAdapter(max_retries=retry_strategy))
    session.headers.update(base_headers or {})
    return session


def get_with_retry(
    url: str,
    session: Optional[requests.Session] = None,
    params: Optional[dict] = None,
    referer: Optional[str] = None,
    delay_before: bool = True,
) -> requests.Response:
    if delay_before:
        with_delay(0.3, 0.8)
    s = session or requests.Session()
    headers = {"User-Agent": next_user_agent()}
    if referer:
        headers["Referer"] = referer

    @retry_with_backoff(max_attempts=3, min_wait=1.0, max_wait=10.0)
    def _get():
        return s.get(url, params=params, headers=headers, timeout=15)

    return _get()
