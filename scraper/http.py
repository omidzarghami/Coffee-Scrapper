from __future__ import annotations

import time
from typing import Any

import requests

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
    "Upgrade-Insecure-Requests": "1",
}


def get(
    url: str,
    *,
    timeout: int = 30,
    retries: int = 3,
    headers: dict[str, str] | None = None,
) -> requests.Response:
    merged = {**DEFAULT_HEADERS, **(headers or {})}
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=merged, timeout=timeout)
            if response.status_code in {429, 500, 502, 503, 504} and attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
                continue
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise
    raise last_error or RuntimeError(f"Failed to fetch {url}")


def post_json(
    url: str,
    payload: dict[str, Any],
    *,
    timeout: int = 60,
    retries: int = 3,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    merged = {
        "Content-Type": "application/json",
        **DEFAULT_HEADERS,
        **(headers or {}),
    }
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            response = requests.post(url, json=payload, headers=merged, timeout=timeout)
            if response.status_code in {429, 500, 502, 503, 504} and attempt < retries - 1:
                time.sleep(2.0 * (attempt + 1))
                continue
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(2.0 * (attempt + 1))
                continue
            raise
    raise last_error or RuntimeError(f"Failed POST {url}")
