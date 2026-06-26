"""분석 결과를 Markdown 리포트로 변환."""
from __future__ import annotations


def _badge(label: str, value: str) -> str:
    return f"`{label}: {value}`"


def build_markdown(date_str: str, data: dict, stats: dict) -> str:
    topics = data.get("topics", [])
    note = data.get("overall_note", "")

    lines: list[str] = []
    lines.append(f"# 📝 아크릴 테크블로그 — 오늘의 글감 추천 ({date_str})")
    lines.append("")
    lines.append(
        f"> 수집 {stats.get('collected', 0)}건 · 신규 {stats.get('new', 0)}건 분석 · "
        f"추천 {len(topics)}개"
    )
    lines.append("")

    if note:
        lines.append("## 🔭 오늘의 흐름")
        lines.append("")
        lines.append(note)
        lines.append("")

    lines.append("## 💡 추천 주제")
    lines.append("")

    if not topics:
        lines.append("_오늘은 추천할 만한 신규 주제를 찾지 못했습니다._")
        lines.append("")
    else:
        for i, t in enumerate(topics, 1):
            lines.append(f"### {i}. {t.get('title', '제목 없음')}")
            lines.append("")
            lines.append(
                " · ".join(
                    [
                        _badge("관련도", f"{t.get('relevance_score', '?')}/100"),
                        _badge("분야", t.get("category", "-")),
                        _badge("난이도", t.get("difficulty", "-")),
                        _badge("형식", t.get("suggested_format", "-")),
                    ]
                )
            )
            lines.append("")
            if t.get("angle"):
                lines.append(f"**기획 방향**: {t['angle']}")
                lines.append("")
            if t.get("why_relevant"):
                lines.append(f"**아크릴과의 연결고리**: {t['why_relevant']}")
                lines.append("")
            if t.get("target_audience"):
                lines.append(f"**타깃 독자**: {t['target_audience']}")
                lines.append("")
            key_points = t.get("key_points", [])
            if key_points:
                lines.append("**다룰 포인트**")
                for kp in key_points:
                    lines.append(f"- {kp}")
                lines.append("")
            sources = t.get("sources", [])
            if sources:
                lines.append("**참고 소스**")
                for s in sources:
                    lines.append(f"- [{s.get('title', s.get('url'))}]({s.get('url')})")
                lines.append("")
            lines.append("---")
            lines.append("")

    lines.append(
        "<sub>이 리포트는 매일 자동 생성됩니다. "
        "소스/관심분야 설정은 `config/` 폴더에서 수정할 수 있습니다.</sub>"
    )
    lines.append("")
    return "\n".join(lines)
