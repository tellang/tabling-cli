from __future__ import annotations

import asyncio
import json
import math
from enum import Enum
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from tabling_cli.client import TablingAPIError, TablingClient
from tabling_cli.models import Restaurant, SearchResult

console = Console()

search_app = typer.Typer(help="매장 검색")

AREA_PRESETS: dict[str, tuple[float, float]] = {
    "pangyo": (37.394, 127.111),
    "seohyeon": (37.389, 127.126),
    "jeongja": (37.368, 127.109),
    "migeun": (37.378, 127.120),
    "yatap": (37.412, 127.128),
}


class AreaPreset(str, Enum):
    pangyo = "pangyo"
    seohyeon = "seohyeon"
    jeongja = "jeongja"
    migeun = "migeun"
    yatap = "yatap"


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """두 좌표 사이의 거리를 km로 반환 (haversine 공식)."""
    R = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lng / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _filter_by_location(
    items: list[Restaurant],
    center_lat: float,
    center_lng: float,
    radius_km: float,
) -> list[Restaurant]:
    """좌표 기반으로 반경 내 매장만 필터링."""
    filtered: list[Restaurant] = []
    for shop in items:
        if shop.latitude is None or shop.longitude is None:
            continue
        dist = _haversine_km(center_lat, center_lng, shop.latitude, shop.longitude)
        if dist <= radius_km:
            filtered.append(shop)
    return filtered


@search_app.command()
def search(
    keyword: str = typer.Argument("", help="검색 키워드"),
    page: int = typer.Option(1, "--page", min=1, help="페이지 번호"),
    page_size: int = typer.Option(20, "--page-size", min=1, max=50, help="페이지 크기"),
    area: Optional[AreaPreset] = typer.Option(None, "--area", help="지역 프리셋 (pangyo, seohyeon, jeongja, migeun, yatap)"),
    lat: Optional[float] = typer.Option(None, "--lat", help="중심 위도 (직접 지정)"),
    lng: Optional[float] = typer.Option(None, "--lng", help="중심 경도 (직접 지정)"),
    radius: float = typer.Option(3.0, "--radius", min=0.1, help="반경 (km, 기본 3km)"),
    as_json: bool = typer.Option(False, "--json", help="JSON 출력"),
) -> None:
    """테이블링 매장을 검색합니다."""
    center_lat: float | None = None
    center_lng: float | None = None

    if area is not None:
        center_lat, center_lng = AREA_PRESETS[area.value]
    if lat is not None:
        center_lat = lat
    if lng is not None:
        center_lng = lng

    if (center_lat is not None) != (center_lng is not None):
        console.print("[red]--lat과 --lng는 함께 지정해야 합니다.[/red]")
        raise typer.Exit(code=1)

    use_location_filter = center_lat is not None and center_lng is not None

    client = TablingClient()

    async def _run() -> dict:
        try:
            return await client.search(
                keyword=keyword,
                page=page,
                page_size=page_size,
            )
        finally:
            await client.close()

    try:
        data = asyncio.run(_run())
    except TablingAPIError as exc:
        console.print(f"[red]API 오류: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    if as_json and not use_location_filter:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    result = SearchResult.model_validate(data)
    total_count = len(result.items)

    if use_location_filter:
        assert center_lat is not None and center_lng is not None
        result.items = _filter_by_location(
            result.items, center_lat, center_lng, radius,
        )
        filtered_count = len(result.items)
        area_label = area.value if area else f"{center_lat:.3f},{center_lng:.3f}"
        console.print(
            f"[dim]{total_count}개 중 {filtered_count}개 매장"
            f" ({area_label} 반경 {radius}km)[/dim]"
        )

        if as_json:
            out = [shop.model_dump(by_alias=True) for shop in result.items]
            print(json.dumps(out, ensure_ascii=False, indent=2))
            return

    title = f"검색 결과 ({len(result.items)}건)"
    table = Table(title=title)
    table.add_column("매장명", style="bold")
    table.add_column("평점", justify="right")
    table.add_column("주소", overflow="fold")
    table.add_column("대기 수", justify="right")
    table.add_column("예약 가능 여부", justify="center")

    for shop in result.items:
        rating = f"{shop.rating:.1f}" if shop.rating is not None else "-"
        waiting_count = shop.waitingCount if shop.waitingCount is not None else 0
        reservation = "-" if shop.useReservation is None else ("가능" if shop.useReservation else "불가")
        name = shop.restaurantName or f"매장 {shop.restaurantIdx or '-'}"
        address = shop.summaryAddress or "-"
        table.add_row(
            name,
            rating,
            address,
            f"{waiting_count}팀",
            reservation,
        )

    if not result.items:
        table.caption = "검색 결과가 없습니다."

    console.print(table)
