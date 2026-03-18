"""런타임 스키마 자체검사 — Agent DX 원칙 3: Runtime Schema Introspection."""
from __future__ import annotations

import json
from typing import Any

import typer
from rich.console import Console

from tabling_cli.models import (
    BrandResult,
    CurationResult,
    Restaurant,
    RestaurantDetail,
    Review,
    ReviewResult,
    SearchResult,
    WaitlistEntry,
    WaitlistStatus,
)

# stderr 전용 콘솔 (Rich 출력)
err_console = Console(stderr=True)

schema_app = typer.Typer(help="커맨드 스키마 자체검사 (JSON)")

# 커맨드별 스키마 정의 맵
# key: 커맨드 경로 (예: "search", "shop info")
_COMMAND_SCHEMAS: dict[str, dict[str, Any]] = {
    "search": {
        "command": "tabling search",
        "description": "테이블링 매장 검색",
        "parameters": {
            "keyword": {"type": "string", "description": "검색 키워드", "required": False, "default": ""},
            "page": {"type": "integer", "description": "페이지 번호", "required": False, "default": 1, "min": 1},
            "page_size": {"type": "integer", "description": "페이지 크기", "required": False, "default": 20, "min": 1, "max": 50},
            "area": {
                "type": "string",
                "description": "지역 프리셋",
                "required": False,
                "enum": ["pangyo", "seohyeon", "jeongja", "migeun", "yatap"],
            },
            "lat": {"type": "number", "description": "중심 위도", "required": False},
            "lng": {"type": "number", "description": "중심 경도", "required": False},
            "radius": {"type": "number", "description": "반경(km)", "required": False, "default": 3.0, "min": 0.1},
            "format": {"type": "string", "description": "출력 형식", "required": False, "default": "json", "enum": ["json", "table", "compact"]},
            "fields": {"type": "string", "description": "응답 필드 선택 (쉼표 구분)", "required": False},
            "dry_run": {"type": "boolean", "description": "API 미호출, 요청 계획만 출력", "required": False, "default": False},
            "json_body": {"type": "string", "description": "전체 요청 본문 직접 전달 (JSON 문자열)", "required": False},
            "params": {"type": "string", "description": "API 쿼리 파라미터 오버라이드 (JSON 문자열)", "required": False},
        },
        "response_model": SearchResult.model_json_schema(),
        "exit_codes": {
            "0": "성공",
            "1": "API 오류 또는 입력 검증 실패",
            "2": "인증 필요",
        },
    },
    "shop info": {
        "command": "tabling shop info",
        "description": "매장 상세 정보 조회",
        "parameters": {
            "shop_id": {"type": "string", "description": "매장 ID", "required": True},
            "format": {"type": "string", "description": "출력 형식", "required": False, "default": "json", "enum": ["json", "table", "compact"]},
            "fields": {"type": "string", "description": "응답 필드 선택 (쉼표 구분)", "required": False},
            "dry_run": {"type": "boolean", "description": "API 미호출, 요청 계획만 출력", "required": False, "default": False},
            "json_body": {"type": "string", "description": "전체 요청 본문 직접 전달 (JSON 문자열)", "required": False},
            "params": {"type": "string", "description": "API 쿼리 파라미터 오버라이드 (JSON 문자열)", "required": False},
        },
        "response_model": RestaurantDetail.model_json_schema(),
        "exit_codes": {
            "0": "성공",
            "1": "API 오류 또는 입력 검증 실패",
            "2": "인증 필요",
        },
    },
    "waitlist register": {
        "command": "tabling waitlist register",
        "description": "대기열 등록 (placeholder)",
        "parameters": {
            "shop_id": {"type": "string", "description": "매장 ID", "required": True},
            "party_size": {"type": "integer", "description": "인원수", "required": False, "default": 2},
            "format": {"type": "string", "description": "출력 형식", "required": False, "default": "json", "enum": ["json", "table", "compact"]},
            "dry_run": {"type": "boolean", "description": "API 미호출, 요청 계획만 출력", "required": False, "default": False},
            "json_body": {"type": "string", "description": "전체 요청 본문 직접 전달 (JSON 문자열)", "required": False},
        },
        "response_model": WaitlistEntry.model_json_schema(),
        "exit_codes": {
            "0": "성공",
            "1": "API 오류 또는 입력 검증 실패",
            "2": "인증 필요",
        },
    },
    "waitlist cancel": {
        "command": "tabling waitlist cancel",
        "description": "대기열 취소 (placeholder)",
        "parameters": {
            "waitlist_id": {"type": "string", "description": "대기열 ID", "required": True},
            "format": {"type": "string", "description": "출력 형식", "required": False, "default": "json", "enum": ["json", "table", "compact"]},
            "dry_run": {"type": "boolean", "description": "API 미호출, 요청 계획만 출력", "required": False, "default": False},
        },
        "response_model": WaitlistEntry.model_json_schema(),
        "exit_codes": {
            "0": "성공",
            "1": "API 오류 또는 입력 검증 실패",
            "2": "인증 필요",
        },
    },
    "waitlist info": {
        "command": "tabling waitlist info",
        "description": "매장의 대기/원격대기 상태 조회",
        "parameters": {
            "shop_id": {"type": "string", "description": "매장 ID", "required": True},
            "format": {"type": "string", "description": "출력 형식", "required": False, "default": "json", "enum": ["json", "table", "compact"]},
            "fields": {"type": "string", "description": "응답 필드 선택 (쉼표 구분)", "required": False},
            "dry_run": {"type": "boolean", "description": "API 미호출, 요청 계획만 출력", "required": False, "default": False},
        },
        "response_model": RestaurantDetail.model_json_schema(),
        "exit_codes": {
            "0": "성공",
            "1": "API 오류 또는 입력 검증 실패",
            "2": "인증 필요",
        },
    },
    "curations list": {
        "command": "tabling curations list",
        "description": "큐레이션 목록 조회",
        "parameters": {
            "home": {"type": "boolean", "description": "홈 큐레이션만 조회 여부", "required": False, "default": True},
            "format": {"type": "string", "description": "출력 형식", "required": False, "default": "json", "enum": ["json", "table", "compact"]},
            "fields": {"type": "string", "description": "응답 필드 선택 (쉼표 구분)", "required": False},
            "dry_run": {"type": "boolean", "description": "API 미호출, 요청 계획만 출력", "required": False, "default": False},
        },
        "response_model": CurationResult.model_json_schema(),
        "exit_codes": {
            "0": "성공",
            "1": "API 오류 또는 입력 검증 실패",
            "2": "인증 필요",
        },
    },
    "curations restaurants": {
        "command": "tabling curations restaurants",
        "description": "큐레이션 내 매장 목록 조회",
        "parameters": {
            "curation_id": {"type": "string", "description": "큐레이션 ID", "required": True},
            "limit": {"type": "integer", "description": "최대 출력 매장 수", "required": False, "default": 20, "min": 1},
            "format": {"type": "string", "description": "출력 형식", "required": False, "default": "json", "enum": ["json", "table", "compact"]},
            "fields": {"type": "string", "description": "응답 필드 선택 (쉼표 구분)", "required": False},
            "dry_run": {"type": "boolean", "description": "API 미호출, 요청 계획만 출력", "required": False, "default": False},
        },
        "response_model": SearchResult.model_json_schema(),
        "exit_codes": {
            "0": "성공",
            "1": "API 오류 또는 입력 검증 실패",
            "2": "인증 필요",
        },
    },
    "brands list": {
        "command": "tabling brands list",
        "description": "브랜드 목록 조회",
        "parameters": {
            "page": {"type": "integer", "description": "페이지 번호", "required": False, "default": 1, "min": 1},
            "page_size": {"type": "integer", "description": "페이지 크기", "required": False, "default": 10, "min": 1, "max": 50},
            "format": {"type": "string", "description": "출력 형식", "required": False, "default": "json", "enum": ["json", "table", "compact"]},
            "fields": {"type": "string", "description": "응답 필드 선택 (쉼표 구분)", "required": False},
            "dry_run": {"type": "boolean", "description": "API 미호출, 요청 계획만 출력", "required": False, "default": False},
        },
        "response_model": BrandResult.model_json_schema(),
        "exit_codes": {
            "0": "성공",
            "1": "API 오류 또는 입력 검증 실패",
            "2": "인증 필요",
        },
    },
    "status": {
        "command": "tabling status",
        "description": "대기 상태 확인",
        "parameters": {
            "waitlist_id": {"type": "string", "description": "대기열 ID", "required": True},
            "format": {"type": "string", "description": "출력 형식", "required": False, "default": "json", "enum": ["json", "table", "compact"]},
            "fields": {"type": "string", "description": "응답 필드 선택 (쉼표 구분)", "required": False},
            "dry_run": {"type": "boolean", "description": "API 미호출, 요청 계획만 출력", "required": False, "default": False},
        },
        "response_model": WaitlistStatus.model_json_schema(),
        "exit_codes": {
            "0": "성공",
            "1": "API 오류 또는 입력 검증 실패",
            "2": "인증 필요",
        },
    },
}


def _list_commands() -> list[str]:
    """등록된 모든 커맨드 이름 목록 반환."""
    return sorted(_COMMAND_SCHEMAS.keys())


@schema_app.command("show")
def show_schema(
    command: str = typer.Argument(help="스키마를 조회할 커맨드 경로 (예: search, 'shop info')"),
) -> None:
    """커맨드의 파라미터, 응답 타입, exit code를 JSON으로 반환합니다."""
    # 공백 포함 커맨드를 허용하기 위해 정규화
    key = command.strip().lower()

    if key not in _COMMAND_SCHEMAS:
        available = ", ".join(_list_commands())
        err_console.print(
            f"[red]알 수 없는 커맨드: {command!r}[/red]\n"
            f"사용 가능한 커맨드: {available}"
        )
        raise typer.Exit(code=1)

    schema = _COMMAND_SCHEMAS[key]
    print(json.dumps(schema, ensure_ascii=False, indent=2))


@schema_app.command("list")
def list_schemas() -> None:
    """스키마가 등록된 모든 커맨드 목록을 JSON으로 반환합니다."""
    output = {
        "commands": _list_commands(),
        "total": len(_COMMAND_SCHEMAS),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
