"""설정 및 마스킹 유틸리티 — Agent DX 원칙 6: Safety Rails."""
from __future__ import annotations

import re
from typing import Any

from pydantic_settings import BaseSettings


class TablingConfig(BaseSettings):
    model_config = {"env_prefix": "TABLING_"}

    api_base_url: str = "https://mobile-v2-api.tabling.co.kr"
    auth_token: str = ""  # 공개 조회는 토큰 불필요. waitlist 등 인증 필요 시 사용


# 민감정보 필드명 패턴 (대소문자 무시)
_SENSITIVE_FIELD_RE = re.compile(
    r"(auth.?token|token|password|passwd|secret|api.?key|authorization|bearer)",
    re.IGNORECASE,
)

# 마스킹 문자
_MASK = "***"


def mask_value(value: str) -> str:
    """민감정보 값을 마스킹. 앞 4자 노출 후 마스킹."""
    if not value:
        return _MASK
    visible = min(4, len(value) // 2)
    return value[:visible] + _MASK


def mask_sensitive(data: dict[str, Any]) -> dict[str, Any]:
    """
    딕셔너리에서 민감정보 필드를 재귀적으로 마스킹.

    auth_token, token, password 등 민감 필드명을 감지하여 마스킹.
    """
    result: dict[str, Any] = {}
    for key, value in data.items():
        if _SENSITIVE_FIELD_RE.search(key):
            # 문자열이면 마스킹, 아니면 "***"으로 대체
            result[key] = mask_value(str(value)) if isinstance(value, str) else _MASK
        elif isinstance(value, dict):
            # 중첩 딕셔너리 재귀 처리
            result[key] = mask_sensitive(value)
        elif isinstance(value, list):
            # 리스트 내 딕셔너리 재귀 처리
            result[key] = [
                mask_sensitive(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value
    return result


def mask_headers(headers: dict[str, str]) -> dict[str, str]:
    """HTTP 헤더에서 Authorization 등 민감 헤더를 마스킹."""
    return {
        k: (mask_value(v) if _SENSITIVE_FIELD_RE.search(k) else v)
        for k, v in headers.items()
    }
