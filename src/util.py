"""공통 유틸리티: HTTP 요청, HTML 정리, 날짜 파싱."""
from __future__ import annotations

import re
import time
from datetime import datetime, timezone

import requests

USER_AGENT = (
    "AcrylTechBlogAgent/1.0 (+https://github.com/jykim3935-dot/blog; "
    "daily topic recommender)"
)

_session = requests.Session()
_session.headers.update({"User-Agent": USER_AGENT})

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def http_get(url: str, *, timeout: int = 20, **kwargs) -> requests.Response | None:
    """간단한 재시도가 포함된 GET. 실패 시 None 반환(파이프라인을 죽이지 않음)."""
    for attempt in range(3):
        try:
            resp = _session.get(url, timeout=timeout, **kwargs)
            resp.raise_for_status()
            return resp
        except Exception as exc:  # noqa: BLE001 - 어떤 소스 하나가 죽어도 계속 진행
            if attempt == 2:
                print(f"  [warn] GET 실패: {url} ({exc})")
                return None
            time.sleep(2 * (attempt + 1))
    return None


def strip_html(text: str | None) -> str:
    if not text:
        return ""
    text = _TAG_RE.sub(" ", text)
    text = (
        text.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&#39;", "'")
        .replace("&quot;", '"')
    )
    return _WS_RE.sub(" ", text).strip()


def truncate(text: str, limit: int = 350) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "…"


def struct_time_to_iso(parsed) -> str | None:
    """feedparser의 *_parsed (time.struct_time)을 ISO 날짜 문자열로."""
    if not parsed:
        return None
    try:
        dt = datetime.fromtimestamp(time.mktime(parsed), tz=timezone.utc)
        return dt.date().isoformat()
    except Exception:  # noqa: BLE001
        return None
