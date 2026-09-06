from __future__ import annotations

import random
import time
from typing import Iterable
from urllib.parse import urlparse

from scraper import gcr, wcp
from scraper.models import Article


def detect_source(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "gcrmag.com" in host:
        return "gcr"
    if "worldcoffeeportal.com" in host:
        return "wcp"
    raise ValueError(f"منبع پشتیبانی‌نشده: {url}")


def fetch_article(url: str) -> Article:
    source = detect_source(url)
    if source == "gcr":
        return gcr.fetch_article(url)
    return wcp.fetch_article(url)


def list_latest(limit: int = 12) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    # Prefer Global Coffee Report tech sections, then World Coffee Portal.
    rows.extend(gcr.list_latest(limit=max(limit, 10), tech_first=True))
    rows.extend(wcp.list_latest(limit=max(limit, 10)))
    rows.sort(
        key=lambda row: (int(row.get("tech_score") or 0), row.get("published_at") or ""),
        reverse=True,
    )
    return rows[:limit]


def fetch_new_articles(
    *,
    max_articles: int,
    skip_urls: Iterable[str] = (),
    delay_min: float = 1.2,
    delay_max: float = 2.4,
    prefer_tech: bool = True,
) -> list[Article]:
    skip = {u.rstrip("/") for u in skip_urls}
    listed = list_latest(limit=max(max_articles * 10, 30))
    if prefer_tech:
        listed.sort(
            key=lambda row: (int(row.get("tech_score") or 0), row.get("published_at") or ""),
            reverse=True,
        )

    picked: list[Article] = []
    for item in listed:
        if len(picked) >= max_articles:
            break
        if item["url"].rstrip("/") in skip:
            continue
        try:
            article = fetch_article(item["url"])
        except Exception:
            continue
        if not article.title:
            continue
        if prefer_tech and article.tech_score <= 0 and len(picked) == 0:
            # Keep looking for a tech-leaning piece first.
            continue
        picked.append(article)
        if len(picked) < max_articles:
            time.sleep(random.uniform(delay_min, delay_max))

    if picked:
        return picked

    # Fallback: any unseen article if no tech hits remain.
    for item in listed:
        if item["url"].rstrip("/") in skip:
            continue
        try:
            article = fetch_article(item["url"])
        except Exception:
            continue
        if article.title:
            return [article]
    return []
