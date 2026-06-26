"""Reddit 컬렉터 (공개 .json 엔드포인트, 인증 불필요)."""
from __future__ import annotations

from ..util import http_get, truncate
from .base import Item


def collect(cfg: dict) -> list[Item]:
    subs = cfg.get("subreddits", [])
    period = cfg.get("time", "day")
    limit = int(cfg.get("limit_per_sub", 12))

    items: list[Item] = []
    for sub in subs:
        url = f"https://www.reddit.com/r/{sub}/top.json?t={period}&limit={limit}"
        resp = http_get(url)
        if resp is None:
            continue
        try:
            children = resp.json().get("data", {}).get("children", [])
        except Exception as exc:  # noqa: BLE001
            print(f"    [warn] reddit JSON 파싱 실패 r/{sub}: {exc}")
            continue

        for child in children:
            d = child.get("data", {})
            title = d.get("title")
            if not title:
                continue
            permalink = d.get("permalink", "")
            # 외부 링크가 있으면 그쪽을, 없으면 reddit 토론 링크를
            external = d.get("url_overridden_by_dest") or d.get("url")
            discussion = f"https://www.reddit.com{permalink}"
            link = external if external and "reddit.com" not in external else discussion
            items.append(
                Item(
                    title=title,
                    url=link,
                    source=f"Reddit r/{sub}",
                    source_type="reddit",
                    summary=truncate(d.get("selftext", "")),
                    score=float(d.get("score", 0)),
                    extra={"discussion": discussion, "num_comments": d.get("num_comments", 0)},
                )
            )
    return items
