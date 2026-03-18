"""출력 형식 관련 공통 유틸리티 — Agent DX 원칙 1: JSON-First Output."""
from __future__ import annotations

import json
from enum import Enum
from typing import Any


class OutputFormat(str, Enum):
    """출력 형식 열거형."""
    json = "json"       # JSON (기본, stdout으로 파이프 호환)
    table = "table"     # Rich 테이블 (stderr)
    compact = "compact"  # 한 줄 JSON (stdout)


def filter_fields(data: Any, fields: str | None) -> Any:
    """
    --fields 옵션에 따라 응답 필드를 선택.

    fields: "name,rating,address" 형태의 쉼표 구분 문자열
    """
    if not fields:
        return data

    field_list = [f.strip() for f in fields.split(",") if f.strip()]
    if not field_list:
        return data

    if isinstance(data, dict):
        return {k: v for k, v in data.items() if k in field_list}
    elif isinstance(data, list):
        return [
            {k: v for k, v in item.items() if k in field_list}
            if isinstance(item, dict) else item
            for item in data
        ]
    return data


def print_json(data: Any, compact: bool = False) -> None:
    """JSON을 stdout으로 출력 (파이프 호환)."""
    if compact:
        print(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))
