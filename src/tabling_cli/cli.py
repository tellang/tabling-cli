"""메인 CLI 엔트리포인트 — Agent DX 7대 원칙 적용."""
from __future__ import annotations

import asyncio
import json
from typing import Optional

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
from tabling_cli.output import OutputFormat, filter_fields, print_json
from tabling_cli.schema import schema_app
from tabling_cli.validate import InputValidationError, sanitize_identifier

# stderr 전용 콘솔 — Rich 출력 (테이블, 에러 메시지)
err_console = Console(stderr=True)

app = typer.Typer(
    name="tabling",
    help="테이블링 비공식 CLI",
    no_args_is_help=True,
)

# 서브앱 등록
app.add_typer(search_app, name="search")
app.add_typer(shop_app, name="shop")
app.add_typer(waitlist_app, name="waitlist")
app.add_typer(curations_app, name="curations")
app.add_typer(brands_app, name="brands")
app.add_typer(schema_app, name="schema")  # 원칙 3: Runtime Schema Introspection


@app.command()
def status(
    waitlist_id: str = typer.Argument(help="대기열 ID"),
    format: OutputFormat = typer.Option(
        OutputFormat.json, "--format", "-f",
        help="출력 형식: json(기본), table, compact",
    ),
    fields: Optional[str] = typer.Option(
        None, "--fields",
        help="응답 필드 선택 (쉼표 구분, 예: id,shop_name,rank)",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run",
        help="API 미호출, 요청 계획만 출력 (원칙 6: Safety Rails)",
    ),
    # 하위호환: 기존 --json 플래그 유지
    as_json: bool = typer.Option(False, "--json", hidden=True, help="JSON 출력 (deprecated: --format json 사용)"),
) -> None:
    """대기 상태를 확인합니다."""
    # 입력 검증 (원칙 4: Input Hardening)
    try:
        waitlist_id = sanitize_identifier(waitlist_id, "waitlist_id")
    except InputValidationError as exc:
        err_console.print(f"[red]입력 오류: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    # --json 플래그 하위호환 처리
    if as_json:
        format = OutputFormat.json

    # dry-run 모드 (원칙 6)
    if dry_run:
        plan = {
            "dry_run": True,
            "method": "GET",
            "path": f"/v1/waitlist/{waitlist_id}",
            "params": {},
        }
        print_json(plan)
        return

    client = TablingClient()

    async def _run() -> dict:
        try:
            return await client.get_waitlist_status(waitlist_id)
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
    ws = WaitlistStatus.model_validate(data)
    content = (
        f"매장: [bold]{ws.shop_name}[/bold]\n"
        f"인원: {ws.party_size}명\n"
        f"현재 순위: {ws.rank}번째\n"
        f"예상 대기: {ws.estimated_wait}\n"
        f"상태: {ws.status}"
    )
    err_console.print(Panel(content, title=f"대기 상태 ({ws.id})"))


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
        "  schema    커맨드 스키마 자체검사\n"
        "  status    대기 상태 확인\n"
        "  version   버전 출력"
    )
