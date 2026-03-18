from __future__ import annotations

import asyncio
import json

import typer
from rich.console import Console
from rich.table import Table

from tabling_cli.client import TablingAPIError, TablingClient
from tabling_cli.models import BrandResult

console = Console()

brands_app = typer.Typer(help="브랜드 탐색")


@brands_app.command("list")
def list_brands(
    page: int = typer.Option(1, "--page", min=1, help="페이지 번호"),
    page_size: int = typer.Option(10, "--page-size", min=1, max=50, help="페이지 크기"),
    as_json: bool = typer.Option(False, "--json", help="JSON 출력"),
) -> None:
    """브랜드 목록을 조회합니다."""
    client = TablingClient()

    async def _run() -> dict:
        try:
            return await client.get_brands(page=page, size=page_size)
        finally:
            await client.close()

    try:
        data = asyncio.run(_run())
    except TablingAPIError as exc:
        console.print(f"[red]API 오류: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

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

    console.print(table)
