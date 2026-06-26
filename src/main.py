"""엔트리포인트: 수집 -> 중복제거 -> 분석 -> Markdown 리포트 저장.

실행: python -m src.main
필요 환경변수: ANTHROPIC_API_KEY
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

from . import analyzer, dedup, report
from .collectors import collect_all
from .config import REPORTS_DIR, extra_urls, load_profile, load_sources


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

    print("[4/4] 리포트 저장 중...")
    stats = {"collected": len(items), "new": len(new_items)}
    markdown = report.build_markdown(date_str, data, stats)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / f"{date_str}.md"
    out_path.write_text(markdown, encoding="utf-8")
    print(f"  저장 완료: {out_path}")

    # 추천에 사용된 소스 URL을 '본 것'으로 기록(다음 실행에서 중복 방지)
    used_urls: list[str] = []
    for t in data.get("topics", []):
        for s in t.get("sources", []):
            if s.get("url"):
                used_urls.append(s["url"])
    dedup.save_seen(seen, used_urls)

    _update_index(date_str, len(data.get("topics", [])))
    print("=== 완료 ===")
    return 0


def _update_index(date_str: str, n_topics: int) -> None:
    """reports/README.md 에 최신 리포트 링크를 위에 추가한다."""
    index = REPORTS_DIR / "README.md"
    header = "# 📚 일일 글감 추천 리포트\n\n"
    entry = f"- [{date_str}](./{date_str}.md) — 추천 {n_topics}개\n"

    existing = ""
    if index.exists():
        text = index.read_text(encoding="utf-8")
        existing = text[len(header):] if text.startswith(header) else text
    # 같은 날짜 줄이 이미 있으면 갱신
    lines = [ln for ln in existing.splitlines(keepends=True) if f"({date_str}.md)" not in ln]
    index.write_text(header + entry + "".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
