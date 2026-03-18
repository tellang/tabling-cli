"""매장 정보 커맨드 — Agent DX 7대 원칙 적용."""
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

shop_app = typer.Typer(help="매장 정보")


@shop_app.command()
def info(
    shop_id: str = typer.Argument(help="매장 ID"),
    format: OutputFormat = typer.Option(
        OutputFormat.json, "--format", "-f",
        help="출력 형식: json(기본), table, compact",
    ),
    fields: Optional[str] = typer.Option(
        None, "--fields",
        help="응답 필드 선택 (쉼표 구분, 예: name,rating,address)",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run",
        help="API 미호출, 요청 계획만 출력 (원칙 6: Safety Rails)",
    ),
    json_body: Optional[str] = typer.Option(
        None, "--json-body",
        help="전체 요청 본문 직접 전달 (JSON 문자열, 원칙 2: Raw Payload Passthrough)",
    ),
    params: Optional[str] = typer.Option(
        None, "--params",
        help="API 쿼리 파라미터 오버라이드 (JSON 문자열, 원칙 2)",
    ),
    # 하위호환: 기존 --json 플래그 유지
    as_json: bool = typer.Option(False, "--json", hidden=True, help="JSON 출력 (deprecated: --format json 사용)"),
) -> None:
    """매장 상세 정보를 조회합니다."""
    # 입력 검증 (원칙 4: Input Hardening)
    try:
        shop_id = sanitize_identifier(shop_id, "shop_id")
    except InputValidationError as exc:
        err_console.print(f"[red]입력 오류: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    # --json 플래그 하위호환 처리
    if as_json:
        format = OutputFormat.json

    # --params 파싱 (원칙 2)
    parsed_params: dict[str, Any] | None = None
    if params:
        try:
            parsed_params = json.loads(params)
        except json.JSONDecodeError as exc:
            err_console.print(f"[red]--params 파싱 오류: {exc}[/red]")
            raise typer.Exit(code=1) from exc

    # dry-run 모드 (원칙 6)
    if dry_run:
        plan: dict[str, Any] = {
            "dry_run": True,
            "method": "GET",
            "path": f"/v1/restaurant/{shop_id}",
            "params": parsed_params or {},
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
    categories = shop.categories
    if isinstance(categories, list):
        category_text = ", ".join(categories) if categories else "-"
    else:
        category_text = categories or "-"
    flag = lambda value: "-" if value is None else ("가능" if value else "불가")

    detail = Table.grid(padding=(0, 1))
    detail.add_row("카테고리", category_text)
    detail.add_row("주소", shop.address or "-")
    detail.add_row("전화", shop.tel or "-")
    detail.add_row("평점", f"{shop.rating:.1f}" if shop.rating is not None else "-")
    detail.add_row(
        "리뷰 수",
        f"{shop.reviewTotalCount:,}" if shop.reviewTotalCount is not None else "-",
    )
    detail.add_row("매장 상태", shop.restaurantStatusLabel or shop.restaurantStatus or "-")
    detail.add_row("대기 가능", flag(shop.useWaiting))
    detail.add_row("원격 대기 가능", flag(shop.useRemoteWaiting))
    detail.add_row("현재 대기", f"{shop.waitingCount or 0}팀")
    detail.add_row(
        "원격 대기 상태",
        shop.remoteWaitingLabel or shop.remoteWaitingStatus or "-",
    )
    detail.add_row("예약 가능", flag(shop.useReservation))
    detail.add_row("예약 상태", shop.reservationLabel or shop.reservationStatus or "-")
    if shop.waitingScopeMessage:
        detail.add_row("대기 안내", shop.waitingScopeMessage)

    err_console.print(
        Panel(
            detail,
            title=f"{shop.name} (#{shop.idx})",
            subtitle=shop.excerpt or "",
            expand=False,
        )
    )
