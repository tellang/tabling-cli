from __future__ import annotations

import asyncio
import json

import typer
from rich.console import Console
from rich.table import Table

from tabling_cli.client import TablingAPIError, TablingClient
from tabling_cli.models import CurationResult, SearchResult

console = Console()

curations_app = typer.Typer(help="큐레이션 탐색")


@curations_app.command("list")
def list_curations(
    home: bool = typer.Option(
        True,
        "--home/--all",
        help="홈 큐레이션만 조회할지 여부",
    ),
    as_json: bool = typer.Option(False, "--json", help="JSON 출력"),
) -> None:
    """큐레이션 목록을 조회합니다."""
    client = TablingClient()

    async def _run() -> dict:
        try:
            return await client.get_curations(home=home)
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

    console.print(table)


@curations_app.command()
def restaurants(
    curation_id: str = typer.Argument(help="큐레이션 ID"),
    limit: int = typer.Option(20, "--limit", min=1, help="출력할 최대 매장 수"),
    as_json: bool = typer.Option(False, "--json", help="JSON 출력"),
) -> None:
    """큐레이션 내 매장 목록을 조회합니다."""
    client = TablingClient()

    async def _run() -> dict:
        try:
            return await client.get_curation_restaurants(curation_id)
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

    console.print(table)
