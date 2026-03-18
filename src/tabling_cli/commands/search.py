"""매장 검색 커맨드 — Agent DX 7대 원칙 적용."""
from __future__ import annotations

import asyncio
import json
import math
from enum import Enum
from typing import Any, Optional

import typer
from rich.console import Console
from rich.table import Table

from tabling_cli.client import TablingAPIError, TablingClient
from tabling_cli.models import Restaurant, SearchResult
from tabling_cli.output import OutputFormat, filter_fields, print_json
from tabling_cli.validate import InputValidationError, sanitize_text

# stderr 전용 콘솔 — Rich 출력 (테이블, 에러 메시지)
err_console = Console(stderr=True)

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
    area: Optional[AreaPreset] = typer.Option(
        None, "--area",
        help="지역 프리셋 (pangyo, seohyeon, jeongja, migeun, yatap)",
    ),
    lat: Optional[float] = typer.Option(None, "--lat", help="중심 위도 (직접 지정)"),
    lng: Optional[float] = typer.Option(None, "--lng", help="중심 경도 (직접 지정)"),
    radius: float = typer.Option(3.0, "--radius", min=0.1, help="반경 (km, 기본 3km)"),
    format: OutputFormat = typer.Option(
        OutputFormat.json, "--format", "-f",
        help="출력 형식: json(기본), table, compact",
    ),
    fields: Optional[str] = typer.Option(
        None, "--fields",
        help="응답 필드 선택 (쉼표 구분, 예: restaurantName,rating,summaryAddress)",
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
    """테이블링 매장을 검색합니다."""
    # 입력 검증 (원칙 4: Input Hardening)
    if keyword:
        try:
            keyword = sanitize_text(keyword, "keyword")
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

    # --params 파싱 (원칙 2)
    parsed_params: dict[str, Any] | None = None
    if params:
        try:
            parsed_params = json.loads(params)
        except json.JSONDecodeError as exc:
            err_console.print(f"[red]--params 파싱 오류: {exc}[/red]")
            raise typer.Exit(code=1) from exc

    center_lat: float | None = None
    center_lng: float | None = None

    if area is not None:
        center_lat, center_lng = AREA_PRESETS[area.value]
    if lat is not None:
        center_lat = lat
    if lng is not None:
        center_lng = lng

    if (center_lat is not None) != (center_lng is not None):
        err_console.print("[red]--lat과 --lng는 함께 지정해야 합니다.[/red]")
        raise typer.Exit(code=1)

    use_location_filter = center_lat is not None and center_lng is not None

    # --json-body가 있으면 그것을 요청 본문으로 사용, 없으면 기본 본문 조립
    request_body: dict[str, Any] = parsed_body if parsed_body is not None else {
        "keyword": keyword or "",
        "page": page,
        "pageSize": page_size,
    }

    # dry-run 모드 (원칙 6)
    if dry_run:
        plan: dict[str, Any] = {
            "dry_run": True,
            "method": "POST",
            "path": "/v1/search/restaurants/map",
            "body": request_body,
        }
        if parsed_params:
            plan["query_params"] = parsed_params
        if center_lat is not None:
            plan["location_filter"] = {
                "center_lat": center_lat,
                "center_lng": center_lng,
                "radius_km": radius,
            }
        print_json(plan)
        return

    client = TablingClient()

    async def _run() -> dict:
        try:
            if parsed_body is not None:
                # 원칙 2: json_body 직접 전달
                return await client._request(
                    "POST", "/v1/search/restaurants/map", json=parsed_body
                )
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
        # 에러를 stderr로 분리 (원칙 1)
        err_console.print(f"[red]API 오류: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    result = SearchResult.model_validate(data)
    total_count = len(result.items)

    if use_location_filter:
        assert center_lat is not None and center_lng is not None
        result.items = _filter_by_location(
            result.items, center_lat, center_lng, radius,
        )
        filtered_count = len(result.items)
        area_label = area.value if area else f"{center_lat:.3f},{center_lng:.3f}"

        if format in (OutputFormat.json, OutputFormat.compact):
            # stdout에는 JSON만 (원칙 1)
            out: list[dict[str, Any]] = [
                shop.model_dump(by_alias=True) for shop in result.items
            ]
            # --fields 필드 선택 (원칙 5)
            filtered_out = filter_fields(out, fields)
            print_json(filtered_out, compact=(format == OutputFormat.compact))
        else:
            # table 형식은 stderr (원칙 1)
            err_console.print(
                f"[dim]{total_count}개 중 {filtered_count}개 매장"
                f" ({area_label} 반경 {radius}km)[/dim]"
            )
            _print_search_table(result.items)
        return

    # --fields 필드 선택 (원칙 5)
    if format in (OutputFormat.json, OutputFormat.compact):
        filtered_data = filter_fields(data, fields)
        print_json(filtered_data, compact=(format == OutputFormat.compact))
        return

    # table 형식 (stderr)
    _print_search_table(result.items)


def _print_search_table(items: list[Restaurant]) -> None:
    """매장 목록을 Rich 테이블로 stderr 출력."""
    title = f"검색 결과 ({len(items)}건)"
    table = Table(title=title)
    table.add_column("매장명", style="bold")
    table.add_column("평점", justify="right")
    table.add_column("주소", overflow="fold")
    table.add_column("대기 수", justify="right")
    table.add_column("예약 가능 여부", justify="center")

    for shop in items:
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

    if not items:
        table.caption = "검색 결과가 없습니다."

    # stderr로 출력 (원칙 1)
    err_console = Console(stderr=True)
    err_console.print(table)
