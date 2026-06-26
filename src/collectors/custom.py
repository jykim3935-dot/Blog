"""사용자가 직접 넣은 URL 컬렉터.

- RSS/Atom 피드면 항목들을 가져오고,
- 일반 웹페이지면 <title> 과 meta description 을 추출해 한 건으로 만든다.
"""
from __future__ import annotations

import re

import feedparser

from ..util import http_get, strip_html, struct_time_to_iso, truncate
from .base import Item

_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_DESC_RE = re.compile(
    r'<meta[^>]+(?:name|property)=["\'](?:description|og:description)["\'][^>]*'
    r'content=["\'](.*?)["\']',
    re.IGNORECASE | re.DOTALL,
)


def collect(urls: list[str]) -> list[Item]:
    items: list[Item] = []
    for url in urls:
        resp = http_get(url)
        if resp is None:
            continue

        content_type = resp.headers.get("Content-Type", "")
        body = resp.text

        # 1) RSS/Atom 피드인지 먼저 시도
        if "xml" in content_type or "<rss" in body[:500].lower() or "<feed" in body[:500].lower():
            parsed = feedparser.parse(body)
            if parsed.entries:
                for entry in parsed.entries[:10]:
                    title = strip_html(entry.get("title"))
                    link = entry.get("link")
                    if not title or not link:
                        continue
                    items.append(
                        Item(
                            title=title,
                            url=link,
                            source="내 소스(피드)",
                            source_type="custom",
                            summary=truncate(strip_html(entry.get("summary"))),
                            published=struct_time_to_iso(entry.get("published_parsed")),
                        )
                    )
                continue

        # 2) 일반 페이지: 제목 + 설명 추출
        title_match = _TITLE_RE.search(body)
        desc_match = _DESC_RE.search(body)
        title = strip_html(title_match.group(1)) if title_match else url
        desc = strip_html(desc_match.group(1)) if desc_match else ""
        items.append(
            Item(
                title=title,
                url=url,
                source="내 소스(페이지)",
                source_type="custom",
                summary=truncate(desc),
            )
        )
    return items
