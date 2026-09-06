from __future__ import annotations

import json
import os
import re
from typing import Any

from scraper.http import post_json

API_ROOT = "https://generativelanguage.googleapis.com/v1beta/models"
FREE_TIER_MODELS = (
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-flash-latest",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
)

SYSTEM_PROMPT = """You are a Persian coffee-industry news editor for a Telegram channel like SorrisoCoffee.
Translate the English article teaser into fluent, journalistic Farsi.

Rules:
- Keep facts; do not invent details that are not in the source.
- Transcribe well-known brand names naturally (Starbucks=استارباکس, Meta=متا, Sodexo=سودکسو).
- Headline must be punchy and news-like, without emoji.
- Split the body into short numbered news sections suitable for Telegram.
- Return JSON only with this shape:
{
  "headline_fa": "...",
  "sections": [
    {"title": "short section title without number", "text": "1-3 Farsi paragraphs"}
  ]
}
"""


class GeminiError(RuntimeError):
    pass


def translate_article(
    *,
    title: str,
    standfirst: str,
    public_text: str,
    source: str,
    api_key: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    key = api_key or os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise GeminiError("GEMINI_API_KEY is missing. Copy .env.example to .env and add a free AI Studio key.")

    preferred = (model or os.getenv("GEMINI_MODEL") or FREE_TIER_MODELS[0]).strip()
    models = [preferred, *[m for m in FREE_TIER_MODELS if m != preferred]]

    user_prompt = (
        f"Source: {source}\n"
        f"Title: {title}\n"
        f"Standfirst: {standfirst}\n\n"
        f"Public teaser:\n{public_text}"
    )
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0.35,
            "responseMimeType": "application/json",
        },
    }

    last_error: Exception | None = None
    for name in models:
        try:
            data = post_json(
                f"{API_ROOT}/{name}:generateContent?key={key}",
                payload,
                timeout=90,
            )
            text = _extract_text(data)
            parsed = _parse_json(text)
            parsed["model"] = name
            return parsed
        except Exception as exc:  # noqa: BLE001 — try next free-tier model
            last_error = exc
            continue
    raise GeminiError(f"All free-tier Gemini models failed. Last error: {last_error}")


def _extract_text(data: dict[str, Any]) -> str:
    candidates = data.get("candidates") or []
    if not candidates:
        raise GeminiError(f"Empty Gemini response: {data}")
    parts = (((candidates[0] or {}).get("content") or {}).get("parts")) or []
    chunks = [p.get("text", "") for p in parts if p.get("text")]
    text = "\n".join(chunks).strip()
    if not text:
        raise GeminiError("Gemini returned no text")
    return text


def _parse_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    parsed = json.loads(cleaned)
    headline = (parsed.get("headline_fa") or "").strip()
    sections = parsed.get("sections") or []
    if not headline or not isinstance(sections, list):
        raise GeminiError("Gemini JSON is missing headline_fa or sections")
    normalized = []
    for item in sections:
        if not isinstance(item, dict):
            continue
        title = (item.get("title") or "").strip()
        body = (item.get("text") or "").strip()
        if title and body:
            normalized.append({"title": title, "text": body})
    if not normalized:
        raise GeminiError("Gemini JSON has no usable sections")
    return {"headline_fa": headline, "sections": normalized}
