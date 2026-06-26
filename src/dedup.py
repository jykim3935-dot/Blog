"""중복 방지: 과거에 추천한(또는 본) URL을 기억해 같은 주제 반복을 줄인다."""
from __future__ import annotations

import json
from pathlib import Path

from .config import REPORTS_DIR

SEEN_PATH = REPORTS_DIR / "seen.json"
MAX_SEEN = 4000  # 너무 커지지 않게 최근 것만 유지


def _normalize(url: str) -> str:
    url = (url or "").strip().lower()
    for prefix in ("https://", "http://", "www."):
        if url.startswith(prefix):
            url = url[len(prefix):]
    return url.rstrip("/").split("?")[0].split("#")[0]


def load_seen() -> set[str]:
    if not SEEN_PATH.exists():
        return set()
    try:
        return set(json.loads(SEEN_PATH.read_text(encoding="utf-8")))
    except Exception:  # noqa: BLE001
        return set()


def filter_new(items, seen: set[str]):
    """이미 본 URL은 제외."""
    out = []
    for it in items:
        if _normalize(it.url) not in seen:
            out.append(it)
    return out


def save_seen(seen: set[str], new_urls: list[str]) -> None:
    for u in new_urls:
        seen.add(_normalize(u))
    # 최근 MAX_SEEN개만 유지 (집합이라 순서는 없지만 상한선만 둠)
    trimmed = list(seen)[-MAX_SEEN:]
    SEEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    SEEN_PATH.write_text(
        json.dumps(trimmed, ensure_ascii=False, indent=0), encoding="utf-8"
    )
