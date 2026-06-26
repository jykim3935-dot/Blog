"""설정 로딩 (config/*.yaml + 환경변수 + 사용자 소스 파일)."""
from __future__ import annotations

import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
REPORTS_DIR = ROOT / "reports"


def _load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_sources() -> dict:
    return _load_yaml(CONFIG_DIR / "sources.yaml")


def load_profile() -> dict:
    return _load_yaml(CONFIG_DIR / "profile.yaml")


def extra_urls(sources: dict) -> list[str]:
    """custom_urls(yaml) + config/my_sources.txt + EXTRA_SOURCE_URLS(env) 합치기."""
    urls: list[str] = list(sources.get("custom_urls") or [])

    my_file = CONFIG_DIR / "my_sources.txt"
    if my_file.exists():
        for line in my_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)

    env_urls = os.environ.get("EXTRA_SOURCE_URLS", "")
    for part in env_urls.split(","):
        part = part.strip()
        if part:
            urls.append(part)

    # 중복 제거(순서 유지)
    seen, result = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            result.append(u)
    return result


def model_id() -> str:
    return os.environ.get("MODEL", "claude-opus-4-8")
