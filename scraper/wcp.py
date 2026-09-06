from __future__ import annotations

import random
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from typing import Iterable
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scraper.http import get

NEWS_SITEMAP = "https://www.worldcoffeeportal.com/sitemap-news"
SOURCE_NAME_EN = "World Coffee Portal"
SOURCE_NAME_FA = "ورلد کافی پورتال"
NS = {
    "sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
    "news": "http://www.google.com/schemas/sitemap-news/0.9",
}


@dataclass
class Article:
    url: str
    title: str
    standfirst: str
    public_text: str
    image_url: str
    published_at: str
    tags: list[str]
    source_en: str = SOURCE_NAME_EN
    source_fa: str = SOURCE_NAME_FA

    def to_dict(self) -> dict:
        return asdict(self)


def list_latest(limit: int = 20) -> list[dict[str, str]]:
    xml_text = get(NEWS_SITEMAP).text
    root = ET.fromstring(xml_text)
    items: list[dict[str, str]] = []
    for url_el in root.findall("sm:url", NS):
        loc = (url_el.findtext("sm:loc", default="", namespaces=NS) or "").strip()
        news_el = url_el.find("news:news", NS)
        if not loc or news_el is None:
            continue
        title = news_el.findtext("news:title", default="", namespaces=NS) or ""
        published = news_el.findtext("news:publication_date", default="", namespaces=NS) or ""
        keywords = news_el.findtext("news:keywords", default="", namespaces=NS) or ""
        items.append(
            {
                "url": loc,
                "title": title.strip(),
                "published_at": published.strip(),
                "keywords": keywords.strip(),
            }
        )
    items.sort(key=lambda row: row["published_at"], reverse=True)
    return items[:limit]


def fetch_article(url: str) -> Article:
    html = get(url).text
    soup = BeautifulSoup(html, "lxml")

    title = _meta(soup, "og:title") or _text(soup.select_one("h1.c-topper__headline"))
    standfirst = _meta(soup, "og:description") or _text(soup.select_one("p.c-topper__standfirst"))
    image_url = _meta(soup, "og:image") or _attr(soup.select_one("img.c-feature-image"), "src")
    published = _meta(soup, "article:published_time") or _attr(
        soup.select_one("time.c-timestamp"), "datetime"
    )
    if published and len(published) == 10:
        published = f"{published}T00:00:00+00:00"

    tags = [_text(a) for a in soup.select(".c-topper__tag a") if _text(a)]
    public_text = _public_body(soup, standfirst)

    if image_url:
        image_url = urljoin(url, image_url)

    return Article(
        url=url,
        title=title.strip(),
        standfirst=standfirst.strip(),
        public_text=public_text.strip(),
        image_url=image_url,
        published_at=published,
        tags=tags,
    )


def fetch_new_articles(
    *,
    max_articles: int,
    skip_urls: Iterable[str] = (),
    delay_min: float = 1.2,
    delay_max: float = 2.4,
) -> list[Article]:
    skip = {u.rstrip("/") for u in skip_urls}
    listed = list_latest(limit=max(max_articles * 4, 12))
    picked: list[Article] = []
    for item in listed:
        if len(picked) >= max_articles:
            break
        if item["url"].rstrip("/") in skip:
            continue
        article = fetch_article(item["url"])
        if not article.title:
            continue
        picked.append(article)
        if len(picked) < max_articles:
            time.sleep(random.uniform(delay_min, delay_max))
    return picked


def _public_body(soup: BeautifulSoup, standfirst: str) -> str:
    content = soup.select_one("div.c-content")
    if content is None:
        return standfirst

    raw = str(content)
    public_html = raw.split("<!--members-only-->")[0]
    public_soup = BeautifulSoup(public_html, "lxml")
    paragraphs = [
        " ".join(p.get_text(" ", strip=True).split())
        for p in public_soup.find_all("p")
        if p.get_text(strip=True)
    ]

    unique: list[str] = []
    seen: set[str] = set()
    for para in paragraphs:
        key = para.casefold()
        if key in seen:
            continue
        seen.add(key)
        unique.append(para)

    # Only the publicly visible teaser — not the paywalled remainder.
    teaser = unique[:3]
    if standfirst and standfirst.casefold() not in seen:
        teaser = [standfirst.strip(), *teaser][:3]
    return "\n\n".join(teaser).strip() or standfirst


def _meta(soup: BeautifulSoup, prop: str) -> str:
    tag = soup.find("meta", attrs={"property": prop}) or soup.find("meta", attrs={"name": prop})
    return (tag.get("content") or "").strip() if tag else ""


def _text(node) -> str:
    return node.get_text(" ", strip=True) if node else ""


def _attr(node, name: str) -> str:
    return (node.get(name) or "").strip() if node else ""
