"""대기열 관리 커맨드 — Agent DX 7대 원칙 적용."""
from __future__ import annotations

import asyncio
import json
from typing import Any, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from tabling_cli.client import TablingAPIError, TablingClient
from tabling_cli.models import RestaurantDetail
from tabling_cli.output import OutputFormat, filter_fields, print_json
from tabling_cli.validate import InputValidationError, sanitize_identifier

# stderr 전용 콘솔 — Rich 출력 (테이블, 에러 메시지)
err_console = Console(stderr=True)

waitlist_app = typer.Typer(help="대기열 관리")


@waitlist_app.command()
def register(
    shop_id: str = typer.Argument(help="매장 ID"),
    party_size: int = typer.Option(2, "--party-size", "-p", help="인원수"),
    format: OutputFormat = typer.Option(
        OutputFormat.json, "--format", "-f",
        help="출력 형식: json(기본), table, compact",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run",
        help="API 미호출, 요청 계획만 출력 (원칙 6: Safety Rails)",
    ),
    json_body: Optional[str] = typer.Option(
        None, "--json-body",
        help="전체 요청 본문 직접 전달 (JSON 문자열, 원칙 2: Raw Payload Passthrough)",
    ),
    # 하위호환: 기존 --json 플래그 유지
    as_json: bool = typer.Option(False, "--json", hidden=True, help="JSON 출력 (deprecated: --format json 사용)"),
) -> None:
    """대기열에 등록합니다. (모바일 앱 전용 API - placeholder)"""
    # 입력 검증 (원칙 4: Input Hardening)
    try:
        shop_id = sanitize_identifier(shop_id, "shop_id")
    except InputValidationError as exc:
        err_console.print(f"[red]입력 오류: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    # --json 플래그 하위호환 처리
    if as_json:
        format = OutputFormat.json

    # --json-body 파싱 (원칙 2)
    parsed_body: dict[str, Any] | None = None
    if json_body:
        try:
            parsed_body = json.loads(json_body)
        except json.JSONDecodeError as exc:
            err_console.print(f"[red]--json-body 파싱 오류: {exc}[/red]")
            raise typer.Exit(code=1) from exc

    # 변경 작업: 사용자 확인 필요 표시 (원칙 6: Safety Rails)
    # dry-run 모드
    if dry_run:
        plan: dict[str, Any] = {
            "dry_run": True,
            "method": "POST",
            "path": f"/v1/restaurant/{shop_id}/waitlist",
            "body": parsed_body or {"partySize": party_size},
            "warning": "대기열 등록은 변경 작업입니다. 모바일 앱 인증 세션 전용 기능입니다.",
        }
        print_json(plan)
        return

    payload = {
        "ok": False,
        "shopId": shop_id,
        "partySize": party_size,
        "message": "대기열 등록은 모바일 앱 인증 세션 전용 기능입니다.",
    }

    if format == OutputFormat.compact:
        print_json(payload, compact=True)
        return
    if format == OutputFormat.json:
        print_json(payload)
        return

    # table 형식 (stderr)
    err_console.print(
        Panel(
            "대기열 등록은 모바일 앱 인증 세션 전용 기능입니다.\n"
            "현재 CLI에서는 조회 기능만 지원합니다.",
            title="미구현 (placeholder)",
            border_style="yellow",
        )
    )


@waitlist_app.command()
def cancel(
    waitlist_id: str = typer.Argument(help="대기열 ID"),
    format: OutputFormat = typer.Option(
        OutputFormat.json, "--format", "-f",
        help="출력 형식: json(기본), table, compact",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run",
        help="API 미호출, 요청 계획만 출력 (원칙 6: Safety Rails)",
    ),
    # 하위호환: 기존 --json 플래그 유지
    as_json: bool = typer.Option(False, "--json", hidden=True, help="JSON 출력 (deprecated: --format json 사용)"),
) -> None:
    """대기열을 취소합니다. (모바일 앱 전용 API - placeholder)"""
    # 입력 검증 (원칙 4: Input Hardening)
    try:
        waitlist_id = sanitize_identifier(waitlist_id, "waitlist_id")
    except InputValidationError as exc:
        err_console.print(f"[red]입력 오류: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    # --json 플래그 하위호환 처리
    if as_json:
        format = OutputFormat.json

    # 변경 작업: dry-run 모드 (원칙 6)
    if dry_run:
        plan: dict[str, Any] = {
            "dry_run": True,
            "method": "DELETE",
            "path": f"/v1/waitlist/{waitlist_id}",
            "warning": "대기열 취소는 변경 작업입니다. 모바일 앱 인증 세션 전용 기능입니다.",
        }
        print_json(plan)
        return

    payload = {
        "ok": False,
        "waitlistId": waitlist_id,
        "message": "대기열 취소는 모바일 앱 인증 세션 전용 기능입니다.",
    }

    if format == OutputFormat.compact:
        print_json(payload, compact=True)
        return
    if format == OutputFormat.json:
        print_json(payload)
        return

    # table 형식 (stderr)
    err_console.print(
        Panel(
            f"대기열 취소는 모바일 앱 인증 세션 전용 기능입니다.\n대상 ID: {waitlist_id}",
            title="미구현 (placeholder)",
            border_style="yellow",
        )
    )


@waitlist_app.command()
def info(
    shop_id: str = typer.Argument(help="매장 ID"),
    format: OutputFormat = typer.Option(
        OutputFormat.json, "--format", "-f",
        help="출력 형식: json(기본), table, compact",
    ),
    fields: Optional[str] = typer.Option(
        None, "--fields",
        help="응답 필드 선택 (쉼표 구분, 예: useWaiting,waitingCount)",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run",
        help="API 미호출, 요청 계획만 출력 (원칙 6: Safety Rails)",
    ),
    # 하위호환: 기존 --json 플래그 유지
    as_json: bool = typer.Option(False, "--json", hidden=True, help="JSON 출력 (deprecated: --format json 사용)"),
) -> None:
    """매장의 대기/원격대기 상태를 조회합니다."""
    # 입력 검증 (원칙 4: Input Hardening)
    try:
        shop_id = sanitize_identifier(shop_id, "shop_id")
    except InputValidationError as exc:
        err_console.print(f"[red]입력 오류: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    # --json 플래그 하위호환 처리
    if as_json:
        format = OutputFormat.json

    # dry-run 모드 (원칙 6)
    if dry_run:
        plan: dict[str, Any] = {
            "dry_run": True,
            "method": "GET",
            "path": f"/v1/restaurant/{shop_id}",
            "params": {},
        }
        print_json(plan)
        return

    client = TablingClient()

    async def _run() -> dict:
        try:
            return await client.get_shop(shop_id)
        finally:
            await client.close()

    try:
        data = asyncio.run(_run())
    except TablingAPIError as exc:
        # 에러를 stderr로 분리 (원칙 1)
        err_console.print(f"[red]API 오류: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    # --fields 필드 선택 (원칙 5)
    filtered = filter_fields(data, fields)

    # JSON-First: json/compact는 stdout, table은 stderr (원칙 1)
    if format == OutputFormat.compact:
        print_json(filtered, compact=True)
        return
    if format == OutputFormat.json:
        print_json(filtered)
        return

    # table 형식 (stderr)
    shop = RestaurantDetail.model_validate(data)
    flag = lambda value: "-" if value is None else ("가능" if value else "불가")
    table = Table(title=f"대기 정보 - {shop.name} (#{shop.idx})")
    table.add_column("항목", style="bold")
    table.add_column("값")
    table.add_row("매장 상태", shop.restaurantStatusLabel or shop.restaurantStatus or "-")
    table.add_row("대기 기능", flag(shop.useWaiting))
    table.add_row("원격 대기", flag(shop.useRemoteWaiting))
    table.add_row("현재 대기", f"{shop.waitingCount or 0}팀")
    table.add_row(
        "원격 대기 상태",
        shop.remoteWaitingLabel or shop.remoteWaitingStatus or "-",
    )
    table.add_row("예약 기능", flag(shop.useReservation))
    table.add_row("예약 상태", shop.reservationLabel or shop.reservationStatus or "-")
    if shop.waitingScopeMessage:
        table.add_row("대기 안내", shop.waitingScopeMessage)

    err_console.print(table)
