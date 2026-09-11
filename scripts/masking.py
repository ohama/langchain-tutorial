"""출력물에서 비밀 값과 홈 경로를 지우는 표준 라이브러리 전용 유틸리티.

이 모듈은 러너(run_examples.py)와 누출 스캐너(check_leaks.py)가 공유한다.
"""
from __future__ import annotations

import os
import re

SECRET_ENV_VARS = ("LLM_API_KEY", "LITELLM_API_KEY", "OPENAI_API_KEY", "LANGSMITH_API_KEY")

KEY_MASK = "***MASKED_API_KEY***"
TOKEN_MASK = "***MASKED***"
HOME_MASK = "~"

_SK_TOKEN_RE = re.compile(r"\bsk-[A-Za-z0-9_\-]{8,}")
_BEARER_TOKEN_RE = re.compile(r"(?i)\b(Bearer\s+)[A-Za-z0-9._~+/\-]{8,}=*")
_USERS_PATH_RE = re.compile(r"/Users/[A-Za-z0-9_][^/\s\"'<>]*")
_HOME_DIR_PATH_RE = re.compile(r"/home/[A-Za-z0-9_][^/\s\"'<>]*")


def collect_secrets(extra: tuple[str, ...] | list[str] = ()) -> list[str]:
    """환경변수(SECRET_ENV_VARS)와 extra에서 비어 있지 않은 값을 모아 중복 제거,
    긴 값부터 정렬해서 반환한다."""
    values = []
    for name in SECRET_ENV_VARS:
        value = os.environ.get(name, "")
        if value:
            value = value.strip()
        if value:
            values.append(value)
    for value in extra:
        if value:
            value = value.strip()
        if value:
            values.append(value)

    deduped = sorted(set(values), key=len, reverse=True)
    return deduped


def mask_text(text: str, secrets, home: str | None = None) -> str:
    """secrets/토큰 패턴/홈 경로를 순서대로 치환한다."""
    result = text

    # 1. 리터럴 비밀 값 치환 (긴 값부터, 길이와 무관하게 항상 치환)
    for secret in sorted(secrets, key=len, reverse=True):
        if not secret:
            continue
        result = result.replace(secret, KEY_MASK)

    # 2. sk-... 토큰
    result = _SK_TOKEN_RE.sub(f"sk-{TOKEN_MASK}", result)

    # 3. Bearer ... 토큰
    result = _BEARER_TOKEN_RE.sub(rf"\1{TOKEN_MASK}", result)

    # 4. 명시적 홈 경로 리터럴
    home_value = home if home is not None else str(__import__("pathlib").Path.home())
    if home_value:
        result = re.sub(re.escape(home_value), HOME_MASK, result)

    # 5. 일반적인 /Users/... , /home/... 경로
    result = _USERS_PATH_RE.sub(HOME_MASK, result)
    result = _HOME_DIR_PATH_RE.sub(HOME_MASK, result)

    return result


def find_leaks(text: str, secrets, home: str | None = None) -> list[str]:
    """text에 남아 있는 누출 종류만 반환한다 (매칭된 값 자체는 절대 반환하지 않음)."""
    kinds: list[str] = []

    # 마스킹 토큰 자체가 리터럴 비밀 검사의 오탐(예: 비밀 값이 "MASKED" 같은 부분 문자열인
    # 경우)을 일으키지 않도록, 먼저 마스킹 토큰들을 제거한 사본으로 리터럴 비밀을 검사한다.
    scrub_for_literal = text.replace(KEY_MASK, "").replace(TOKEN_MASK, "")
    for secret in secrets:
        if secret and secret in scrub_for_literal:
            kinds.append("literal-secret")
            break

    if _SK_TOKEN_RE.search(text):
        kinds.append("sk-token")

    if _BEARER_TOKEN_RE.search(text):
        kinds.append("bearer-token")

    home_value = home if home is not None else str(__import__("pathlib").Path.home())
    if home_value and home_value in text:
        kinds.append("home-path")

    if _USERS_PATH_RE.search(text):
        kinds.append("users-path")
    elif _HOME_DIR_PATH_RE.search(text):
        kinds.append("users-path")

    return kinds
