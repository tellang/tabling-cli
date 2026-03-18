from __future__ import annotations

import asyncio
import json

import typer
from rich.console import Console
from rich.panel import Panel

from tabling_cli import __version__
from tabling_cli.client import TablingAPIError, TablingClient
from tabling_cli.commands.brands import brands_app
from tabling_cli.commands.curations import curations_app
from tabling_cli.commands.search import search_app
from tabling_cli.commands.shop import shop_app
from tabling_cli.commands.waitlist import waitlist_app
from tabling_cli.models import WaitlistStatus

console = Console()

app = typer.Typer(
    name="tabling",
    help="테이블링 비공식 CLI",
    no_args_is_help=True,
)

app.add_typer(search_app, name="search")
app.add_typer(shop_app, name="shop")
app.add_typer(waitlist_app, name="waitlist")
app.add_typer(curations_app, name="curations")
app.add_typer(brands_app, name="brands")


@app.command()
def status(
    waitlist_id: str = typer.Argument(help="대기열 ID"),
    as_json: bool = typer.Option(False, "--json", help="JSON 출력"),
) -> None:
    """대기 상태를 확인합니다."""
    client = TablingClient()

    async def _run() -> dict:
        try:
            return await client.get_waitlist_status(waitlist_id)
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

    ws = WaitlistStatus.model_validate(data)
    content = (
        f"매장: [bold]{ws.shop_name}[/bold]\n"
        f"인원: {ws.party_size}명\n"
        f"현재 순위: {ws.rank}번째\n"
        f"예상 대기: {ws.estimated_wait}\n"
        f"상태: {ws.status}"
    )
    console.print(Panel(content, title=f"대기 상태 ({ws.id})"))


@app.command()
def version() -> None:
    """버전을 출력합니다."""
    typer.echo(f"tabling-cli v{__version__}")


@app.command()
def overview() -> None:
    """CLI 개요를 출력합니다."""
    typer.echo(
        f"tabling-cli v{__version__}\n"
        "테이블링 비공식 CLI\n\n"
        "사용 가능한 명령어:\n"
        "  search    매장 검색\n"
        "  shop      매장 정보 조회\n"
        "  waitlist  대기열 관리\n"
        "  curations 큐레이션 탐색\n"
        "  brands    브랜드 탐색\n"
        "  status    대기 상태 확인\n"
        "  version   버전 출력"
    )
