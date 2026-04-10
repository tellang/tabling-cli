"""브랜드 탐색 커맨드 — Agent DX 7대 원칙 적용."""
from __future__ import annotations

import asyncio
import json
from typing import Any, Optional

import typer
from rich.console import Console
from rich.table import Table

from tabling_cli.client import TablingAPIError, TablingClient
from tabling_cli.models import BrandResult
from tabling_cli.output import OutputFormat, filter_fields, print_json

# stderr 전용 콘솔 — Rich 출력 (테이블, 에러 메시지)
err_console = Console(stderr=True)

brands_app = typer.Typer(help="브랜드 탐색")


@brands_app.command("list")
def list_brands(
    page: int = typer.Option(1, "--page", min=1, help="페이지 번호"),
    page_size: int = typer.Option(10, "--page-size", min=1, max=50, help="페이지 크기"),
    format: OutputFormat = typer.Option(
        OutputFormat.json, "--format", "-f",
        help="출력 형식: json(기본), table, compact",
    ),
    fields: Optional[str] = typer.Option(
        None, "--fields",
        help="응답 필드 선택 (쉼표 구분, 예: name,categories,status)",
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
    """브랜드 목록을 조회합니다."""
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
            "path": "/v1/brands/",
            "params": parsed_params or {"page": page, "pageSize": page_size},
        }
        print_json(plan)
        return

    client = TablingClient()

    async def _run() -> dict:
        try:
            if parsed_params:
                # 원칙 2: --params 쿼리 파라미터 오버라이드
                return await client._request("GET", "/v1/brands/", params=parsed_params)
            return await client.get_brands(page=page, size=page_size)
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
    result = BrandResult.model_validate(data)
    table = Table(title=f"브랜드 목록 ({result.totalCount}건)")
    table.add_column("ID", style="dim")
    table.add_column("브랜드명", style="bold")
    table.add_column("카테고리")
    table.add_column("소개", overflow="fold")
    table.add_column("상태", justify="center")
    table.add_column("인기", justify="center")

    for brand in result.items:
        categories = brand.categories
        if isinstance(categories, list):
            category_text = ", ".join(categories) if categories else "-"
        else:
            category_text = categories or "-"

        table.add_row(
            brand.id,
            brand.name,
            category_text,
            brand.excerpt or "-",
            brand.status or "-",
            "Y" if brand.isPopular else "N",
        )

    if not result.items:
        table.caption = "조회된 브랜드가 없습니다."

    err_console.print(table)
