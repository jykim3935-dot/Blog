"""Claude(claude-opus-4-8)로 수집 항목을 분석해 블로그 주제를 선별한다."""
from __future__ import annotations

import json

import anthropic

from .config import model_id

# 1차(LLM 호출 전) 키워드 점수로 상위 N개만 추려 토큰/비용을 통제
MAX_ITEMS_TO_LLM = 110

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "topics": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "블로그 글 제목(한국어)"},
                    "angle": {"type": "string", "description": "어떤 관점/구성으로 풀어갈지"},
                    "why_relevant": {
                        "type": "string",
                        "description": "아크릴과 왜 관련 있는지",
                    },
                    "category": {"type": "string", "description": "분야 태그"},
                    "key_points": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "다룰 핵심 포인트 3~5개",
                    },
                    "suggested_format": {
                        "type": "string",
                        "description": "예: 심층 해설 / 튜토리얼 / 동향 정리 / 의견글",
                    },
                    "difficulty": {"type": "string", "description": "입문/중급/고급"},
                    "target_audience": {"type": "string"},
                    "relevance_score": {
                        "type": "integer",
                        "description": "아크릴 관련도 0~100",
                    },
                    "sources": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "url": {"type": "string"},
                            },
                            "required": ["title", "url"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": [
                    "title",
                    "angle",
                    "why_relevant",
                    "category",
                    "key_points",
                    "suggested_format",
                    "difficulty",
                    "target_audience",
                    "relevance_score",
                    "sources",
                ],
                "additionalProperties": False,
            },
        },
        "overall_note": {
            "type": "string",
            "description": "오늘의 전반적 흐름/트렌드 한두 문단 요약",
        },
    },
    "required": ["topics", "overall_note"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """\
당신은 AI 전문기업 '아크릴(Acryl)'의 테크블로그 편집장을 돕는 콘텐츠 전략가입니다.
매일 외신·AI 커뮤니티·arXiv·빅테크 블로그 등에서 수집한 항목들을 분석해,
아크릴 블로그에 쓰면 좋을 '글감(주제)'을 선별하고 구체적인 글 기획안을 제안합니다.

원칙:
- 아크릴의 관심 분야와의 관련성을 최우선으로 판단합니다.
- 단순 제품 홍보나 가십이 아니라, 엔지니어/연구자/도입 실무자에게 인사이트를 주는 주제를 고릅니다.
- 비슷한 항목 여러 개를 묶어 하나의 깊이 있는 주제로 종합해도 좋습니다.
- 한국어로, 실무에 바로 도움이 되도록 구체적으로 작성합니다.
- 각 주제에는 근거가 된 원문 소스를 sources에 정확한 URL로 첨부합니다.
"""


def _keyword_prescore(items, profile: dict):
    """LLM 호출 전 키워드 기반으로 거칠게 점수화해 상위 항목만 추린다."""
    keywords = [k.lower() for k in profile.get("keywords", [])]
    for it in items:
        text = f"{it.title} {it.summary}".lower()
        kw_hits = sum(1 for k in keywords if k in text)
        # 인기도(score)는 출처별 스케일이 달라 로그 비슷하게 약하게만 반영
        popularity = min(it.score, 500) / 500.0
        it.score = kw_hits * 2.0 + popularity
    items.sort(key=lambda it: it.score, reverse=True)
    return items


def _format_items(items) -> str:
    lines = []
    for i, it in enumerate(items, 1):
        meta = it.published or "날짜미상"
        lines.append(
            f"[{i}] ({it.source} · {meta})\n"
            f"  제목: {it.title}\n"
            f"  요약: {it.summary or '(요약 없음)'}\n"
            f"  URL: {it.url}"
        )
    return "\n".join(lines)


def _build_user_prompt(items, profile: dict) -> str:
    company = profile.get("company", {})
    focus = "\n".join(f"  - {x}" for x in profile.get("focus_areas", []))
    avoid = "\n".join(f"  - {x}" for x in profile.get("avoid", []))
    n_topics = int(profile.get("topics_per_day", 8))

    return f"""\
## 회사 정보
{company.get('name', '아크릴')}
{company.get('one_liner', '')}

## 블로그가 다루고 싶은 핵심 분야
{focus}

## 피하고 싶은 주제
{avoid}

## 독자 / 톤
독자: {profile.get('audience', '')}
톤: {profile.get('tone', '')}

## 오늘 수집된 항목 ({len(items)}건)
{_format_items(items)}

## 요청
위 항목들을 분석해서, 아크릴 테크블로그에 쓰면 좋을 주제를 **관련도 높은 순으로 정확히 {n_topics}개** 선별하세요.
- 각 주제는 schema에 맞춰 구체적인 기획안으로 작성합니다.
- relevance_score(0~100)는 아크릴 관심 분야와의 관련도입니다.
- sources에는 근거가 된 위 항목들의 실제 URL을 1개 이상 넣으세요.
- overall_note에는 오늘 전반적인 AI 업계 흐름을 1~2문단으로 정리하세요.
"""


def analyze(items, profile: dict) -> dict:
    """수집 항목 -> 구조화된 추천 결과(dict)."""
    if not items:
        return {"topics": [], "overall_note": "오늘은 새로 수집된 항목이 없습니다."}

    items = _keyword_prescore(list(items), profile)[:MAX_ITEMS_TO_LLM]

    client = anthropic.Anthropic()  # ANTHROPIC_API_KEY 환경변수 사용
    resp = client.messages.create(
        model=model_id(),
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_user_prompt(items, profile)}],
        output_config={"format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
    )

    text = next((b.text for b in resp.content if b.type == "text"), "")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"LLM 응답 JSON 파싱 실패: {exc}\n응답: {text[:500]}") from exc

    usage = resp.usage
    print(
        f"  [llm] 입력 {usage.input_tokens} / 출력 {usage.output_tokens} 토큰, "
        f"주제 {len(data.get('topics', []))}개"
    )
    return data
