"""큐레이션 탐색 커맨드 — Agent DX 7대 원칙 적용."""
from __future__ import annotations

import asyncio
import json
from typing import Any, Optional

import typer
from rich.console import Console
from rich.table import Table

from tabling_cli.client import TablingAPIError, TablingClient
from tabling_cli.models import CurationResult, SearchResult
from tabling_cli.output import OutputFormat, filter_fields, print_json
from tabling_cli.validate import InputValidationError, sanitize_identifier

# stderr 전용 콘솔 — Rich 출력 (테이블, 에러 메시지)
err_console = Console(stderr=True)

curations_app = typer.Typer(help="큐레이션 탐색")


@curations_app.command("list")
def list_curations(
    home: bool = typer.Option(
        True,
        "--home/--all",
        help="홈 큐레이션만 조회할지 여부",
    ),
    format: OutputFormat = typer.Option(
        OutputFormat.json, "--format", "-f",
        help="출력 형식: json(기본), table, compact",
    ),
    fields: Optional[str] = typer.Option(
        None, "--fields",
        help="응답 필드 선택 (쉼표 구분, 예: id,title,isOn)",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run",
        help="API 미호출, 요청 계획만 출력 (원칙 6: Safety Rails)",
    ),
    params: Optional[str] = typer.Option(
        None, "--params",
        help="API 쿼리 파라미터 오버라이드 (JSON 문자열, 원칙 2)",
    ),
    # 하위호환: 기존 --json 플래그 유지
    as_json: bool = typer.Option(False, "--json", hidden=True, help="JSON 출력 (deprecated: --format json 사용)"),
) -> None:
    """큐레이션 목록을 조회합니다."""
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
            "path": "/v1/curations",
            "params": parsed_params or {"isHome": home},
        }
        print_json(plan)
        return

    client = TablingClient()

    async def _run() -> dict:
        try:
            if parsed_params:
                # 원칙 2: --params 쿼리 파라미터 오버라이드
                return await client._request("GET", "/v1/curations", params=parsed_params)
            return await client.get_curations(home=home)
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
    result = CurationResult.model_validate(data)
    table = Table(title=f"큐레이션 목록 ({result.totalCount}건)")
    table.add_column("ID", style="dim")
    table.add_column("제목", style="bold")
    table.add_column("부제", overflow="fold")
    table.add_column("매장 수", justify="right")
    table.add_column("활성", justify="center")
    table.add_column("이모지", justify="center")

    for curation in result.items:
        table.add_row(
            curation.id,
            curation.title,
            curation.subTitle or "-",
            str(len(curation.restaurantIdxes)),
            "ON" if curation.isOn else "OFF",
            curation.emoji or "-",
        )

    if not result.items:
        table.caption = "조회된 큐레이션이 없습니다."

    err_console.print(table)


@curations_app.command()
def restaurants(
    curation_id: str = typer.Argument(help="큐레이션 ID"),
    limit: int = typer.Option(20, "--limit", min=1, help="출력할 최대 매장 수"),
    format: OutputFormat = typer.Option(
        OutputFormat.json, "--format", "-f",
        help="출력 형식: json(기본), table, compact",
    ),
    fields: Optional[str] = typer.Option(
        None, "--fields",
        help="응답 필드 선택 (쉼표 구분, 예: restaurantName,rating)",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run",
        help="API 미호출, 요청 계획만 출력 (원칙 6: Safety Rails)",
    ),
    # 하위호환: 기존 --json 플래그 유지
    as_json: bool = typer.Option(False, "--json", hidden=True, help="JSON 출력 (deprecated: --format json 사용)"),
) -> None:
    """큐레이션 내 매장 목록을 조회합니다."""
    # 입력 검증 (원칙 4: Input Hardening)
    try:
        curation_id = sanitize_identifier(curation_id, "curation_id")
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
            "path": f"/v1/curation-restaurants/{curation_id}",
            "params": {},
        }
        print_json(plan)
        return

    client = TablingClient()

    async def _run() -> dict:
        try:
            return await client.get_curation_restaurants(curation_id)
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
    result = SearchResult.model_validate(data)
    table = Table(title=f"큐레이션 매장 ({result.total}건)")
    table.add_column("매장명", style="bold")
    table.add_column("평점", justify="right")
    table.add_column("주소", overflow="fold")
    table.add_column("대기 수", justify="right")
    table.add_column("예약", justify="center")

    for shop in result.items[:limit]:
        rating = f"{shop.rating:.1f}" if shop.rating is not None else "-"
        waiting_count = shop.waitingCount if shop.waitingCount is not None else 0
        reservation = "-" if shop.useReservation is None else ("가능" if shop.useReservation else "불가")
        table.add_row(
            shop.restaurantName or f"매장 {shop.restaurantIdx or '-'}",
            rating,
            shop.summaryAddress or "-",
            f"{waiting_count}팀",
            reservation,
        )

    if not result.items:
        table.caption = "조회된 매장이 없습니다."
    elif len(result.items) > limit:
        table.caption = (
            f"전체 {result.total}건 중 API 응답 {len(result.items)}건,"
            f" {limit}개만 출력했습니다."
        )

    err_console.print(table)
