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

waitlist_app = typer.Typer(help="대기열 관리")


@waitlist_app.command()
def register(
    shop_id: str = typer.Argument(help="매장 ID"),
    party_size: int = typer.Option(2, "--party-size", "-p", help="인원수"),
    as_json: bool = typer.Option(False, "--json", help="JSON 출력"),
) -> None:
    """대기열에 등록합니다. (모바일 앱 전용 API - placeholder)"""
    payload = {
        "ok": False,
        "shopId": shop_id,
        "partySize": party_size,
        "message": "대기열 등록은 모바일 앱 인증 세션 전용 기능입니다.",
    }
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    console.print(
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
    as_json: bool = typer.Option(False, "--json", help="JSON 출력"),
) -> None:
    """대기열을 취소합니다. (모바일 앱 전용 API - placeholder)"""
    payload = {
        "ok": False,
        "waitlistId": waitlist_id,
        "message": "대기열 취소는 모바일 앱 인증 세션 전용 기능입니다.",
    }
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    console.print(
        Panel(
            f"대기열 취소는 모바일 앱 인증 세션 전용 기능입니다.\n대상 ID: {waitlist_id}",
            title="미구현 (placeholder)",
            border_style="yellow",
        )
    )


@waitlist_app.command()
def info(
    shop_id: str = typer.Argument(help="매장 ID"),
    as_json: bool = typer.Option(False, "--json", help="JSON 출력"),
) -> None:
    """매장의 대기/원격대기 상태를 조회합니다."""
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

    console.print(table)
