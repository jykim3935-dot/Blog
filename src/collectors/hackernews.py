"""Hacker News 컬렉터 (Algolia Search API, 인증 불필요)."""
from __future__ import annotations

from datetime import datetime, timezone

from ..util import http_get, truncate
from .base import Item

API = "https://hn.algolia.com/api/v1/search_by_date"


def collect(cfg: dict) -> list[Item]:
    queries = cfg.get("queries", ["AI", "LLM"])
    min_points = int(cfg.get("min_points", 50))
    limit = int(cfg.get("limit", 25))

    seen: set[str] = set()
    items: list[Item] = []

    for q in queries:
        params = {
            "query": q,
            "tags": "story",
            "numericFilters": f"points>{min_points}",
            "hitsPerPage": "20",
        }
        resp = http_get(API, params=params)
        if resp is None:
            continue
        try:
            hits = resp.json().get("hits", [])
        except Exception as exc:  # noqa: BLE001
            print(f"    [warn] HN JSON 파싱 실패 (query={q}): {exc}")
            continue

        for hit in hits:
            object_id = hit.get("objectID")
            title = hit.get("title")
            if not object_id or not title or object_id in seen:
                continue
            seen.add(object_id)
            url = hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
            published = None
            ts = hit.get("created_at_i")
            if ts:
                published = datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()
            items.append(
                Item(
                    title=title,
                    url=url,
                    source="Hacker News",
                    source_type="hackernews",
                    summary=truncate(hit.get("story_text", "") or ""),
                    published=published,
                    score=float(hit.get("points", 0)),
                    extra={
                        "discussion": f"https://news.ycombinator.com/item?id={object_id}",
                        "num_comments": hit.get("num_comments", 0),
                    },
                )
            )

    items.sort(key=lambda it: it.score, reverse=True)
    return items[:limit]
