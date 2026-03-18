"""입력 검증 함수 모음 — Agent DX 원칙 4: Input Hardening."""
from __future__ import annotations

import re
import unicodedata


# 제어문자 패턴: ASCII 0x00-0x1F, DEL(0x7F)
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]")

# 위험 유니코드: 제로폭 공백, 방향 오버라이드, 기타 보이지 않는 조작 문자
_DANGEROUS_UNICODE: set[str] = {
    "\u200b",  # ZERO WIDTH SPACE
    "\u200c",  # ZERO WIDTH NON-JOINER
    "\u200d",  # ZERO WIDTH JOINER
    "\u200e",  # LEFT-TO-RIGHT MARK
    "\u200f",  # RIGHT-TO-LEFT MARK
    "\u202a",  # LEFT-TO-RIGHT EMBEDDING
    "\u202b",  # RIGHT-TO-LEFT EMBEDDING
    "\u202c",  # POP DIRECTIONAL FORMATTING
    "\u202d",  # LEFT-TO-RIGHT OVERRIDE
    "\u202e",  # RIGHT-TO-LEFT OVERRIDE
    "\u2060",  # WORD JOINER
    "\u2066",  # LEFT-TO-RIGHT ISOLATE
    "\u2067",  # RIGHT-TO-LEFT ISOLATE
    "\u2068",  # FIRST STRONG ISOLATE
    "\u2069",  # POP DIRECTIONAL ISOLATE
    "\ufeff",  # BOM / ZERO WIDTH NO-BREAK SPACE
}

# 경로 순회 패턴: ../, ..\, %2e%2e 등
_PATH_TRAVERSAL_RE = re.compile(
    r"(\.\.[/\\])|(%2e%2e)|(%252e)|(\.\./)|(\.\.[/\\])",
    re.IGNORECASE,
)

# URL 인코딩 패턴 (% 기반)
_URL_ENCODED_RE = re.compile(r"%[0-9a-fA-F]{2}")

# 이중 인코딩 패턴: %25xx 형태
_DOUBLE_ENCODED_RE = re.compile(r"%25[0-9a-fA-F]{2}", re.IGNORECASE)


class InputValidationError(ValueError):
    """입력 검증 실패 시 발생하는 예외."""


def sanitize_text(value: str, field_name: str = "값") -> str:
    """
    일반 텍스트 입력을 검증하고 NFC 정규화 후 반환.

    - 제어문자 거부 (ASCII 0x00-0x1F, 0x7F)
    - 위험 유니코드 거부
    - 이중 인코딩 방지
    - NFC 정규화 적용
    """
    # NFC 정규화 먼저 적용
    value = unicodedata.normalize("NFC", value)

    # 제어문자 검사
    if _CONTROL_CHARS_RE.search(value):
        raise InputValidationError(
            f"{field_name}에 제어문자(0x00-0x1F, 0x7F)가 포함되어 있습니다."
        )

    # 위험 유니코드 검사
    for char in _DANGEROUS_UNICODE:
        if char in value:
            code_point = f"U+{ord(char):04X}"
            raise InputValidationError(
                f"{field_name}에 위험한 유니코드 문자({code_point})가 포함되어 있습니다."
            )

    # 이중 인코딩 검사 (%25xx 형태)
    if _DOUBLE_ENCODED_RE.search(value):
        raise InputValidationError(
            f"{field_name}에 이중 URL 인코딩이 포함되어 있습니다."
        )

    return value


def sanitize_identifier(value: str, field_name: str = "식별자") -> str:
    """
    shop_id, waitlist_id 등 식별자 입력 검증.

    sanitize_text 규칙에 더해:
    - 경로 순회 문자 거부 (../, ..\\ 등)
    - 슬래시/백슬래시 거부
    """
    # 기본 텍스트 검증 먼저 수행
    value = sanitize_text(value, field_name)

    # 경로 순회 패턴 검사
    if _PATH_TRAVERSAL_RE.search(value):
        raise InputValidationError(
            f"{field_name}에 경로 순회 문자가 포함되어 있습니다."
        )

    # 슬래시/백슬래시 직접 포함 여부 검사
    if "/" in value or "\\" in value:
        raise InputValidationError(
            f"{field_name}에 경로 구분자(/, \\)가 포함되어 있습니다."
        )

    return value
