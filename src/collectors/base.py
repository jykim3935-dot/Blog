"""수집 항목 자료구조 + 전체 컬렉터 오케스트레이션."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional


@dataclass
class Item:
    title: str
    url: str
    source: str          # 사람이 읽는 소스 이름 (예: "NVIDIA Tech Blog")
    source_type: str     # rss / arxiv / reddit / hackernews / custom
    summary: str = ""
    published: Optional[str] = None   # ISO 날짜 (YYYY-MM-DD)
    score: float = 0.0                # 인기도/사전 점수
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def collect_all(sources: dict, custom_urls: list[str]) -> list[Item]:
    """설정된 모든 소스에서 항목 수집. 한 소스가 실패해도 나머지는 계속."""
    # 지연 임포트로 순환참조 방지
    from . import arxiv, custom, hackernews, reddit, rss

    items: list[Item] = []

    def run(label: str, fn):
        try:
            got = fn()
            print(f"  [{label}] {len(got)}건 수집")
            items.extend(got)
        except Exception as exc:  # noqa: BLE001
            print(f"  [{label}] 수집 실패: {exc}")

    if sources.get("rss"):
        run("rss", lambda: rss.collect(sources["rss"]))
    if sources.get("extra_rss"):
        run("extra_rss", lambda: rss.collect(sources["extra_rss"]))
    if sources.get("arxiv"):
        run("arxiv", lambda: arxiv.collect(sources["arxiv"]))
    if sources.get("reddit"):
        run("reddit", lambda: reddit.collect(sources["reddit"]))
    if sources.get("hackernews"):
        run("hackernews", lambda: hackernews.collect(sources["hackernews"]))
    if custom_urls:
        run("custom", lambda: custom.collect(custom_urls))

    return items
