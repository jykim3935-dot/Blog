"""엔트리포인트: 수집 -> 중복제거 -> 분석 -> Markdown + HTML 리포트 + 인덱스.

실행: python -m src.main
필요 환경변수: ANTHROPIC_API_KEY
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from . import analyzer, dedup, report
from .collectors import collect_all
from .config import REPORTS_DIR, extra_urls, load_profile, load_sources

INDEX_JSON = REPORTS_DIR / "index.json"


def _today() -> str:
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    except Exception:  # noqa: BLE001
        return datetime.now(timezone.utc).date().isoformat()


def main() -> int:
    date_str = _today()
    print(f"=== 아크릴 테크블로그 글감 추천 ({date_str}) ===")

    sources = load_sources()
    profile = load_profile()
    custom = extra_urls(sources)

    print("[1/4] 소스 수집 중...")
    items = collect_all(sources, custom)
    print(f"  총 {len(items)}건 수집")

    print("[2/4] 중복 제거 중...")
    seen = dedup.load_seen()
    new_items = dedup.filter_new(items, seen)
    print(f"  신규 {len(new_items)}건 (이미 본 {len(items) - len(new_items)}건 제외)")

    print("[3/4] Claude 분석 중...")
    data = analyzer.analyze(new_items, profile)

    print("[4/4] 리포트 & 인덱스 저장 중...")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    stats = {"collected": len(items), "new": len(new_items)}
    n_topics = len(data.get("topics", []))

    (REPORTS_DIR / f"{date_str}.md").write_text(
        report.build_markdown(date_str, data, stats), encoding="utf-8"
    )
    (REPORTS_DIR / f"{date_str}.html").write_text(
        report.build_html(date_str, data, stats), encoding="utf-8"
    )
    print(f"  저장: {date_str}.md / {date_str}.html (추천 {n_topics}개)")

    _rebuild_index(date_str, n_topics)

    # 추천에 쓰인 소스 URL을 기록 -> 다음 실행 중복 방지
    used = [s["url"] for t in data.get("topics", []) for s in t.get("sources", []) if s.get("url")]
    dedup.save_seen(seen, used)

    print("=== 완료 ===")
    return 0


def _rebuild_index(date_str: str, n_topics: int) -> None:
    """index.json 갱신 후 reports/index.html(목록 페이지)을 다시 생성."""
    entries: dict[str, dict] = {}
    if INDEX_JSON.exists():
        try:
            for e in json.loads(INDEX_JSON.read_text(encoding="utf-8")):
                entries[e["date"]] = e
        except Exception:  # noqa: BLE001
            pass
    entries[date_str] = {"date": date_str, "topics": n_topics}

    ordered = sorted(entries.values(), key=lambda e: e["date"], reverse=True)
    INDEX_JSON.write_text(
        json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (REPORTS_DIR / "index.html").write_text(report.build_index(ordered), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
