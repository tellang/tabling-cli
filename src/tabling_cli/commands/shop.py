from __future__ import annotations

import asyncio
import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from tabling_cli.client import TablingAPIError, TablingClient
from tabling_cli.models import RestaurantDetail

console = Console()

shop_app = typer.Typer(help="매장 정보")


@shop_app.command()
def info(
    shop_id: str = typer.Argument(help="매장 ID"),
    as_json: bool = typer.Option(False, "--json", help="JSON 출력"),
) -> None:
    """매장 상세 정보를 조회합니다."""
    client = TablingClient()

    async def _run() -> dict:
        try:
            return await client.get_shop(shop_id)
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

    console.print(
        Panel(
            detail,
            title=f"{shop.name} (#{shop.idx})",
            subtitle=shop.excerpt or "",
            expand=False,
        )
    )
