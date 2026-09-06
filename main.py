from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from scraper.format_posts import build_posts
from scraper.gemini import GeminiError, translate_article
from scraper.preview import write_preview
from scraper.store import SeenStore, save_json
from scraper.telegram import TelegramError, send_posts
from scraper.wcp import fetch_article, fetch_new_articles, list_latest

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"
console = Console()


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    return float(raw) if raw else default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    return int(raw) if raw else default


def cmd_latest(limit: int) -> None:
    rows = list_latest(limit=limit)
    table = Table(title="آخرین اخبار ورلد کافی پورتال")
    table.add_column("تاریخ")
    table.add_column("عنوان")
    table.add_column("لینک")
    for row in rows:
        table.add_row(row["published_at"][:10], row["title"], row["url"])
    console.print(table)


def cmd_run(*, limit: int, force: bool, dry_run: bool, url: str, send: bool) -> int:
    delay_min = _env_float("DELAY_MIN", 1.2)
    delay_max = _env_float("DELAY_MAX", 2.4)
    seen = SeenStore(OUTPUT / "seen.json")
    skip = [] if force or url else seen.urls

    if url:
        articles = [fetch_article(url)]
    else:
        articles = fetch_new_articles(
            max_articles=limit,
            skip_urls=skip,
            delay_min=delay_min,
            delay_max=delay_max,
        )

    if not articles:
        console.print("[yellow]مقاله جدیدی پیدا نشد.[/yellow]")
        return 0

    table = Table(title=f"{len(articles)} مقاله")
    table.add_column("عنوان")
    table.add_column("تاریخ")
    for article in articles:
        table.add_row(article.title, article.published_at[:10] or "—")
    console.print(table)

    results: list[dict] = []
    for article in articles:
        if dry_run:
            translation = {
                "headline_fa": f"[پیش‌نمایش بدون ترجمه] {article.title}",
                "sections": [{"title": "خلاصه انگلیسی", "text": article.public_text}],
                "model": "dry-run",
            }
        else:
            try:
                translation = translate_article(
                    title=article.title,
                    standfirst=article.standfirst,
                    public_text=article.public_text,
                    source=article.source_en,
                )
            except GeminiError as exc:
                console.print(f"[red]ترجمه ناموفق:[/red] {article.title}\n{exc}")
                continue

        posts = build_posts(article, translation)
        if send:
            if dry_run:
                console.print("[yellow]ارسال تلگرام در --dry-run انجام نمی‌شود.[/yellow]")
            else:
                try:
                    send_posts(posts)
                    console.print("[green]ارسال شد به تلگرام[/green]")
                except TelegramError as exc:
                    console.print(f"[red]ارسال تلگرام ناموفق:[/red] {exc}")
                    return 1

        record = {
            "article": article.to_dict(),
            "translation": translation,
            "posts": posts,
        }
        results.append(record)
        seen.add(article.url)
        console.print(f"[green]آماده[/green] {article.title}")

    if not results:
        return 1

    seen.persist()
    save_json(OUTPUT / "articles.json", results)
    write_preview(OUTPUT / "telegram-board.html", results)
    for record in results:
        slug = record["article"]["url"].rstrip("/").split("/")[-1]
        save_json(OUTPUT / "posts" / f"{slug}.json", record)

    console.print(f"[bold]خروجی JSON:[/bold] {OUTPUT / 'articles.json'}")
    console.print(f"[bold]پیش‌نمایش HTML:[/bold] {OUTPUT / 'telegram-board.html'}")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="اسکرپ اخبار قهوه از World Coffee Portal و ترجمه فارسی با Gemini رایگان."
    )
    parser.add_argument("--list", action="store_true", help="فقط فهرست آخرین تیترها")
    parser.add_argument("--max", "--count", dest="max_articles", type=int, default=0, help="تعداد مقاله (پیش‌فرض MAX_ARTICLES)")
    parser.add_argument("--force", action="store_true", help="حتی مقالات قبلی را دوباره ترجمه کن")
    parser.add_argument("--dry-run", action="store_true", help="فقط اسکرپ؛ بدون Gemini")
    parser.add_argument("--url", default="", help="ترجمه یک لینک مشخص")
    parser.add_argument("--send", action="store_true", help="ارسال پست‌ها به کانال تلگرام")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    load_dotenv(ROOT / ".env")
    args = parse_args(argv)
    limit = args.max_articles or _env_int("MAX_ARTICLES", 3)
    if args.list:
        cmd_latest(limit)
        return 0
    return cmd_run(
        limit=limit,
        force=args.force,
        dry_run=args.dry_run,
        url=args.url,
        send=args.send,
    )


if __name__ == "__main__":
    sys.exit(main())
