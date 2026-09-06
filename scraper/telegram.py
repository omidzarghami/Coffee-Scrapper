from __future__ import annotations

import os
import time
from typing import Any

import requests

PHOTO_CAPTION_LIMIT = 1024


class TelegramError(RuntimeError):
    pass


def send_posts(
    posts: list[dict[str, Any]],
    *,
    token: str | None = None,
    chat_id: str | None = None,
) -> None:
    token = (token or os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    chat_id = (chat_id or os.getenv("TELEGRAM_CHANNEL_ID") or "").strip()
    if not token or not chat_id:
        raise TelegramError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHANNEL_ID is missing.")

    for index, post in enumerate(posts):
        if index:
            time.sleep(1.0)
        image_url = (post.get("image_url") or "").strip()
        text = (post.get("text") or "").strip()
        button_url = (post.get("button_url") or "").strip()
        button_label = (post.get("button_label") or "مطالعه اصل مقاله").strip()
        markup = _keyboard(button_label, button_url) if button_url else None

        if image_url:
            try:
                _api(
                    token,
                    "sendPhoto",
                    {
                        "chat_id": chat_id,
                        "photo": image_url,
                        "caption": text[:PHOTO_CAPTION_LIMIT],
                        **({"reply_markup": markup} if markup else {}),
                    },
                )
                continue
            except TelegramError:
                text = f"{text}\n\n{image_url}"

        _api(
            token,
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": text[:4096],
                "disable_web_page_preview": True,
                **({"reply_markup": markup} if markup else {}),
            },
        )


def _keyboard(label: str, url: str) -> dict[str, Any]:
    return {"inline_keyboard": [[{"text": label, "url": url}]]}


def _api(token: str, method: str, payload: dict[str, Any]) -> dict[str, Any]:
    url = f"https://api.telegram.org/bot{token}/{method}"
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = requests.post(url, json=payload, timeout=45)
            data = response.json()
            if response.status_code in {429, 500, 502, 503, 504} and attempt < 2:
                time.sleep(2.0 * (attempt + 1))
                continue
            if not data.get("ok"):
                raise TelegramError(data.get("description") or f"Telegram {method} failed")
            return data
        except (requests.RequestException, ValueError) as exc:
            last_error = TelegramError(str(exc))
            if attempt < 2:
                time.sleep(2.0 * (attempt + 1))
                continue
            raise last_error from exc
    raise last_error or TelegramError(f"Telegram {method} failed")
