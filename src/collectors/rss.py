"""RSS/Atom 피드 컬렉터 (외신 + 빅테크 블로그 + MLPerf 등)."""
from __future__ import annotations

import feedparser

from ..util import strip_html, struct_time_to_iso, truncate
from .base import Item


def collect(cfg: dict) -> list[Item]:
    limit = int(cfg.get("limit_per_feed", 12))
    items: list[Item] = []

    for feed in cfg.get("feeds", []):
        name = feed.get("name", "RSS")
        url = feed.get("url")
        if not url:
            continue
        try:
            parsed = feedparser.parse(url)
        except Exception as exc:  # noqa: BLE001
            print(f"    [warn] 피드 파싱 실패 {name}: {exc}")
            continue

        for entry in parsed.entries[:limit]:
            link = entry.get("link")
            title = strip_html(entry.get("title"))
            if not link or not title:
                continue
            summary = truncate(strip_html(entry.get("summary") or entry.get("description")))
            published = struct_time_to_iso(
                entry.get("published_parsed") or entry.get("updated_parsed")
            )
            items.append(
                Item(
                    title=title,
                    url=link,
                    source=name,
                    source_type="rss",
                    summary=summary,
                    published=published,
                )
            )
    return items
