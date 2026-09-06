from __future__ import annotations

import random
import re
import time
import xml.etree.ElementTree as ET
from typing import Iterable
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from scraper.http import get
from scraper.models import Article
from scraper.tech import tech_score

SOURCE_NAME_EN = "Global Coffee Report"
SOURCE_NAME_FA = "گلوبال کافی ریپورت"
HOME = "https://www.gcrmag.com"
SITEMAP_INDEX = f"{HOME}/sitemap_index.xml"
TECH_SECTIONS = (
    f"{HOME}/coffee-technology/",
    f"{HOME}/research-development/",
    f"{HOME}/automation-telemetry/",
    f"{HOME}/coffee-roasting-technology/",
)
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def list_latest(limit: int = 20, *, tech_first: bool = True) -> list[dict[str, str]]:
    items: dict[str, dict[str, str]] = {}

    for section in TECH_SECTIONS:
        for row in _list_section(section):
            items[row["url"].rstrip("/")] = row

    for row in _list_sitemap(limit=max(limit * 4, 40)):
        key = row["url"].rstrip("/")
        if key not in items:
            items[key] = row
        else:
            # Keep richer published date / score from sitemap when available.
            if row["published_at"] > items[key]["published_at"]:
                items[key]["published_at"] = row["published_at"]
            items[key]["tech_score"] = str(
                max(int(items[key]["tech_score"]), int(row["tech_score"]))
            )

    ranked = list(items.values())
    if tech_first:
        ranked.sort(
            key=lambda row: (int(row["tech_score"]), row["published_at"]),
            reverse=True,
        )
    else:
        ranked.sort(key=lambda row: row["published_at"], reverse=True)
    return ranked[:limit]


def fetch_article(url: str) -> Article:
    html = get(url).text
    soup = BeautifulSoup(html, "lxml")

    title = _meta(soup, "og:title") or _text(soup.select_one("h1.jeg_post_title, h1"))
    title = re.sub(r"\s*[-|]\s*Global Coffee Report\s*$", "", title, flags=re.I).strip()
    standfirst = _meta(soup, "og:description")
    image_url = _meta(soup, "og:image")
    published = _meta(soup, "article:published_time")
    if published and len(published) == 10:
        published = f"{published}T00:00:00+00:00"

    tags = [
        _text(a)
        for a in soup.select(".jeg_meta_category a, .jeg_post_category a, a[rel='category tag']")
        if _text(a)
    ]
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
        source_en=SOURCE_NAME_EN,
        source_fa=SOURCE_NAME_FA,
        tech_score=tech_score(title, standfirst, " ".join(tags), public_text) + 2,
    )


def fetch_new_articles(
    *,
    max_articles: int,
    skip_urls: Iterable[str] = (),
    delay_min: float = 1.2,
    delay_max: float = 2.4,
) -> list[Article]:
    skip = {u.rstrip("/") for u in skip_urls}
    listed = list_latest(limit=max(max_articles * 8, 24), tech_first=True)
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


def _list_section(section_url: str) -> list[dict[str, str]]:
    html = get(section_url).text
    soup = BeautifulSoup(html, "lxml")
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for a in soup.select("h2 a, h3 a, .jeg_post_title a"):
        href = (a.get("href") or "").strip()
        title = a.get_text(" ", strip=True)
        if not href or not title or not _is_article_url(href):
            continue
        key = href.rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "url": href,
                "title": title,
                "published_at": "",
                "keywords": "technology",
                "source": "gcr",
                "tech_score": str(tech_score(title, "technology") + 5),
            }
        )
    return rows


def _list_sitemap(limit: int = 40) -> list[dict[str, str]]:
    index_xml = get(SITEMAP_INDEX).text
    root = ET.fromstring(index_xml)
    post_maps = [
        (el.findtext("sm:loc", default="", namespaces=NS) or "").strip()
        for el in root.findall("sm:sitemap", NS)
    ]
    post_maps = [u for u in post_maps if "post-sitemap" in u]
    # Newest post sitemaps tend to be last in Yoast indexes.
    candidates: list[dict[str, str]] = []
    for sitemap_url in reversed(post_maps[-2:]):
        xml_text = get(sitemap_url).text
        sm_root = ET.fromstring(xml_text)
        for url_el in sm_root.findall("sm:url", NS):
            loc = (url_el.findtext("sm:loc", default="", namespaces=NS) or "").strip()
            lastmod = (url_el.findtext("sm:lastmod", default="", namespaces=NS) or "").strip()
            if not _is_article_url(loc):
                continue
            slug = loc.rstrip("/").rsplit("/", 1)[-1].replace("-", " ")
            candidates.append(
                {
                    "url": loc,
                    "title": slug,
                    "published_at": lastmod,
                    "keywords": "",
                    "source": "gcr",
                    "tech_score": str(tech_score(slug)),
                }
            )
    candidates.sort(key=lambda row: row["published_at"], reverse=True)
    return candidates[:limit]


def _public_body(soup: BeautifulSoup, standfirst: str) -> str:
    content = soup.select_one(".entry-content, .content-inner, article .content")
    if content is None:
        return standfirst
    paragraphs = [
        " ".join(p.get_text(" ", strip=True).split())
        for p in content.find_all("p")
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
    teaser = unique[:4]
    if standfirst:
        first = unique[0].casefold() if unique else ""
        if standfirst.casefold() not in first and standfirst.casefold() not in seen:
            teaser = [standfirst.strip(), *teaser][:4]
    return "\n\n".join(teaser).strip() or standfirst


ARCHIVE_PATHS = {
    "/coffee-technology",
    "/research-development",
    "/automation-telemetry",
    "/coffee-roasting-technology",
    "/coffee-industry-news",
    "/features",
    "/business-leaders",
    "/coffee-profiles",
    "/coffee-equipment-reviews",
    "/world-coffee-price-market-reports",
    "/sustainability-coffee-industry-issues",
    "/international-coffee-events",
    "/gcr-leaders-symposium",
    "/melbourne-international-coffee-expo",
    "/world-coffee-origins",
    "/about-us",
    "/subscribe",
    "/advertise",
    "/contact-us",
    "/online-subscription",
}


def _is_article_url(url: str) -> bool:
    if not url.startswith(HOME):
        return False
    path = urlparse(url).path.rstrip("/")
    if not path or path.count("/") != 1:
        return False
    if path in ARCHIVE_PATHS:
        return False
    if any(path.startswith(prefix.rstrip("/")) for prefix in ("/tag/", "/author/", "/page/", "/wp-")):
        return False
    return True


def _meta(soup: BeautifulSoup, prop: str) -> str:
    tag = soup.find("meta", attrs={"property": prop}) or soup.find("meta", attrs={"name": prop})
    return (tag.get("content") or "").strip() if tag else ""


def _text(node) -> str:
    return node.get_text(" ", strip=True) if node else ""
