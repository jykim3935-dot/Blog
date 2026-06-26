"""arXiv 최신 논문 컬렉터 (arXiv Atom API)."""
from __future__ import annotations

import feedparser

from ..util import http_get, strip_html, struct_time_to_iso, truncate
from .base import Item

API = "http://export.arxiv.org/api/query"


def collect(cfg: dict) -> list[Item]:
    categories = cfg.get("categories", ["cs.AI", "cs.LG", "cs.CL"])
    max_results = int(cfg.get("max_results", 25))

    search_query = "+OR+".join(f"cat:{c}" for c in categories)
    params = {
        "search_query": search_query,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": str(max_results),
    }
    # arXiv는 search_query의 +,: 를 인코딩하면 안 되므로 직접 쿼리스트링 구성
    query = (
        f"search_query={search_query}"
        f"&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
    )
    resp = http_get(f"{API}?{query}")
    if resp is None:
        return []

    parsed = feedparser.parse(resp.text)
    items: list[Item] = []
    for entry in parsed.entries:
        title = strip_html(entry.get("title"))
        link = entry.get("link")
        if not title or not link:
            continue
        authors = ", ".join(a.get("name", "") for a in entry.get("authors", [])[:3])
        items.append(
            Item(
                title=title,
                url=link,
                source="arXiv",
                source_type="arxiv",
                summary=truncate(strip_html(entry.get("summary"))),
                published=struct_time_to_iso(entry.get("published_parsed")),
                extra={"authors": authors},
            )
        )
    return items
