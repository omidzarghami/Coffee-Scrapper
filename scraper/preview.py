from __future__ import annotations

import html
from pathlib import Path
from typing import Any


def write_preview(path: Path, items: list[dict[str, Any]]) -> None:
    cards = "\n".join(_card(item) for item in items)
    empty = "" if items else "<p class='note'>هنوز مقاله‌ای ترجمه نشده است.</p>"
    doc = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Coffee Scrapper — پست‌های تلگرام</title>
<style>
  :root {{ --bg:#f6f1ea; --ink:#1c1917; --card:#fff; --accent:#6f1d1b; --muted:#7c6f64; }}
  * {{ box-sizing:border-box }}
  body {{ margin:0; font-family:Tahoma, Vazirmatn, sans-serif; background:linear-gradient(160deg,#f6f1ea,#efe4d4); color:var(--ink); padding:24px; }}
  h1 {{ font-size:1.4rem; margin:0 0 8px }}
  .note {{ opacity:.8; margin-bottom:20px; max-width:760px; line-height:1.8 }}
  .grid {{ display:grid; gap:18px; }}
  .article {{ background:var(--card); border-radius:16px; padding:18px; box-shadow:0 10px 28px rgba(0,0,0,.07); }}
  .article h2 {{ margin:0 0 10px; font-size:1.05rem }}
  .meta {{ margin:0 0 12px; color:var(--muted); font-size:.9rem }}
  .posts {{ display:grid; gap:12px; }}
  .post {{ border:1px solid #eadfd3; border-radius:12px; padding:12px; background:#fffaf5; }}
  .post img {{ width:100%; max-height:280px; object-fit:cover; border-radius:10px; margin-bottom:10px }}
  .post pre {{ white-space:pre-wrap; font-family:inherit; margin:0; line-height:1.85 }}
  .btn {{ display:inline-block; margin-top:10px; background:var(--accent); color:#fff; text-decoration:none; padding:9px 12px; border-radius:10px; font-weight:700 }}
</style>
</head>
<body>
  <h1>کانال خبری قهوه — خروجی آماده تلگرام</h1>
  <p class="note">هر کارت یک مقاله تازه از ورلد کافی پورتال است. متن‌ها با Gemini به فارسی ترجمه شده‌اند. دکمه لینک اصل مقاله را باز می‌کند.</p>
  <div class="grid">
    {cards or empty}
  </div>
</body>
</html>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(doc, encoding="utf-8")


def _card(item: dict[str, Any]) -> str:
    article = item["article"]
    posts_html = []
    for post in item["posts"]:
        image = ""
        if post.get("image_url"):
            src = html.escape(post["image_url"])
            image = f'<img src="{src}" alt=""/>'
        button = ""
        if post.get("button_url"):
            href = html.escape(post["button_url"])
            label = html.escape(post.get("button_label") or "مطالعه اصل مقاله")
            button = f'<a class="btn" href="{href}" target="_blank" rel="noopener">{label}</a>'
        body = html.escape(post["text"])
        posts_html.append(f'<div class="post">{image}<pre>{body}</pre>{button}</div>')
    title = html.escape(article.get("title") or "")
    url = html.escape(article.get("url") or "")
    return f"""<article class="article">
      <h2>{title}</h2>
      <p class="meta"><a href="{url}" target="_blank" rel="noopener">{url}</a></p>
      <div class="posts">{''.join(posts_html)}</div>
    </article>"""
