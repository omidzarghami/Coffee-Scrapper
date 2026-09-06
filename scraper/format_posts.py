from __future__ import annotations

from typing import Any

from scraper.jalali import to_jalali_str
from scraper.wcp import Article

TELEGRAM_LIMIT = 3900


def build_posts(article: Article, translation: dict[str, Any]) -> list[dict[str, str]]:
    jalali = to_jalali_str(article.published_at)
    headline = translation["headline_fa"].strip()
    preview = (
        f"☕ {headline}\n\n"
        f"📅 {jalali}\n"
        f"🌐 {article.source_fa}\n\n"
        f"👇 ادامه ترجمه در پیام بعد"
    )
    posts = [
        {
            "kind": "preview",
            "text": preview,
            "image_url": article.image_url,
            "button_label": "🔗 مطالعه اصل مقاله",
            "button_url": article.url,
        }
    ]

    for index, section in enumerate(translation["sections"], start=1):
        chunk = f"📝 {index}- {section['title']}\n\n{section['text']}".strip()
        for piece in _split_telegram(chunk):
            posts.append({"kind": "body", "text": piece, "image_url": "", "button_label": "", "button_url": ""})
    return posts


def _split_telegram(text: str) -> list[str]:
    if len(text) <= TELEGRAM_LIMIT:
        return [text]
    parts: list[str] = []
    remaining = text
    while remaining:
        if len(remaining) <= TELEGRAM_LIMIT:
            parts.append(remaining)
            break
        window = remaining[:TELEGRAM_LIMIT]
        cut = window.rfind("\n\n")
        if cut < 400:
            cut = window.rfind("\n")
        if cut < 400:
            cut = TELEGRAM_LIMIT
        parts.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()
    return parts
