"""분석 결과 -> Markdown + 스타일링된 HTML 리포트 + 인덱스 페이지."""
from __future__ import annotations

import html
import json
from pathlib import Path

from .config import CONFIG_DIR

THEME_PATH = CONFIG_DIR / "report_theme.css"
FONT_LINK = (
    '<link rel="stylesheet" '
    'href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/'
    'dist/web/static/pretendard.min.css">'
)


# =========================================================================
# Markdown (GitHub에서 바로 읽기 좋은 형태)
# =========================================================================
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
            if t.get("key_points"):
                lines.append("**다룰 포인트**")
                for kp in t["key_points"]:
                    lines.append(f"- {kp}")
                lines.append("")
            if t.get("sources"):
                lines.append("**참고 소스**")
                for s in t["sources"]:
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


# =========================================================================
# HTML (디자인 적용 / GitHub Pages 배포용)
# =========================================================================
def _theme_css() -> str:
    try:
        return THEME_PATH.read_text(encoding="utf-8")
    except Exception:  # noqa: BLE001
        return ""


def _esc(text) -> str:
    return html.escape(str(text if text is not None else ""))


def _doc(title: str, body: str) -> str:
    return (
        "<!DOCTYPE html>\n"
        '<html lang="ko">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{_esc(title)}</title>\n"
        f"{FONT_LINK}\n"
        f"<style>\n{_theme_css()}\n</style>\n"
        "</head>\n<body>\n"
        f'<div class="wrap">\n{body}\n</div>\n'
        "</body>\n</html>\n"
    )


def _topic_card(i: int, t: dict) -> str:
    parts = ['<article class="card">']
    parts.append('<div class="card-head">')
    parts.append(f'<div class="rank">{i}</div>')
    parts.append(f"<h3>{_esc(t.get('title', '제목 없음'))}</h3>")
    parts.append("</div>")

    parts.append('<div class="badges">')
    parts.append(
        f'<span class="badge score">관련도 {_esc(t.get("relevance_score", "?"))}/100</span>'
    )
    for label in ("category", "difficulty", "suggested_format"):
        if t.get(label):
            parts.append(f'<span class="badge">{_esc(t[label])}</span>')
    parts.append("</div>")

    def field(label: str, value: str) -> str:
        return (
            f'<div class="field"><span class="label">{label}</span>'
            f"<p>{_esc(value)}</p></div>"
        )

    if t.get("angle"):
        parts.append(field("기획 방향", t["angle"]))
    if t.get("why_relevant"):
        parts.append(field("아크릴과의 연결고리", t["why_relevant"]))
    if t.get("target_audience"):
        parts.append(field("타깃 독자", t["target_audience"]))

    if t.get("key_points"):
        items = "".join(f"<li>{_esc(kp)}</li>" for kp in t["key_points"])
        parts.append(
            '<div class="field"><span class="label">다룰 포인트</span>'
            f'<ul class="points">{items}</ul></div>'
        )

    if t.get("sources"):
        links = "".join(
            f'<a href="{_esc(s.get("url"))}" target="_blank" rel="noopener">'
            f'{_esc(s.get("title", s.get("url")))}</a><br>'
            for s in t["sources"]
        )
        parts.append(
            f'<div class="sources"><span class="label">참고 소스</span>{links}</div>'
        )

    parts.append("</article>")
    return "".join(parts)


def build_html(date_str: str, data: dict, stats: dict) -> str:
    topics = data.get("topics", [])
    note = data.get("overall_note", "")

    body: list[str] = []
    body.append('<header class="masthead">')
    body.append('<span class="eyebrow">Acryl Tech Blog · 오늘의 글감</span>')
    body.append(f"<h1>아크릴 테크블로그 추천 — {_esc(date_str)}</h1>")
    body.append(
        f'<p class="meta">수집 {stats.get("collected", 0)}건 · '
        f'신규 {stats.get("new", 0)}건 분석 · 추천 {len(topics)}개 · '
        f'<a href="./index.html">← 전체 목록</a></p>'
    )
    body.append("</header>")

    if note:
        body.append(
            f'<section class="flow"><h2>🔭 오늘의 흐름</h2><p>{_esc(note)}</p></section>'
        )

    body.append('<h2 class="section-title">추천 주제</h2>')
    if not topics:
        body.append('<div class="empty">오늘은 추천할 만한 신규 주제를 찾지 못했습니다.</div>')
    else:
        for i, t in enumerate(topics, 1):
            body.append(_topic_card(i, t))

    body.append(
        '<footer class="footer">매일 자동 생성됩니다. '
        "설정은 <code>config/</code> 폴더에서 수정할 수 있어요.</footer>"
    )
    return _doc(f"아크릴 글감 추천 {date_str}", "\n".join(body))


def build_index(entries: list[dict]) -> str:
    """entries: [{'date': '2026-06-26', 'topics': 8}, ...] (최신순 정렬됨)"""
    body: list[str] = []
    body.append('<header class="masthead">')
    body.append('<span class="eyebrow">Acryl Tech Blog</span>')
    body.append("<h1>📚 일일 글감 추천</h1>")
    body.append(
        '<p class="meta">외신·AI 커뮤니티·arXiv·빅테크 블로그를 매일 분석해 '
        "블로그 글감을 추천합니다.</p>"
    )
    body.append("</header>")

    body.append('<h2 class="section-title">리포트</h2>')
    if not entries:
        body.append('<div class="empty">아직 생성된 리포트가 없습니다. 곧 첫 리포트가 올라옵니다.</div>')
    else:
        for e in entries:
            date = _esc(e.get("date"))
            n = _esc(e.get("topics", 0))
            body.append(
                '<article class="card"><div class="card-head">'
                f'<h3><a href="./{date}.html" style="color:inherit;text-decoration:none">'
                f"{date}</a></h3></div>"
                f'<div class="badges"><span class="badge">추천 {n}개</span></div>'
                f'<div class="field"><a class="badge score" '
                f'style="text-decoration:none" href="./{date}.html">리포트 보기 →</a></div>'
                "</article>"
            )
    body.append('<footer class="footer">Powered by Claude · 매일 자동 갱신</footer>')
    return _doc("아크릴 테크블로그 — 일일 글감 추천", "\n".join(body))
