"""Typer command-line consumer."""

import asyncio
import logging
import os
import tempfile
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Annotated, Any, cast

import typer
from dotenv import load_dotenv
from pydantic import SecretStr, ValidationError
from rich.console import Console

from sevendtd.admin.builders import (
    prepare_ban,
    prepare_ban_list,
    prepare_give,
    prepare_kick,
    prepare_message,
    prepare_say,
    prepare_search_items,
    prepare_unban,
)
from sevendtd.admin.metadata import BanDurationUnit
from sevendtd.cli.commands.map import create_mosaic, inclusive_range
from sevendtd.cli.errors import exit_code
from sevendtd.cli.output import emit, emit_error, emit_json_line, emit_status
from sevendtd.client import AsyncSevenDTDClient
from sevendtd.config import SevenDTDSettings
from sevendtd.exceptions import SevenDTDCommandError, SevenDTDConfigurationError, SevenDTDError
from sevendtd.models.commands import CommandResult
from sevendtd.models.logs import LogLineEvent, ReconnectPolicy
from sevendtd.models.players import WorldHorizontalPosition

app = typer.Typer(no_args_is_help=True, help="7 Days to Die dedicated-server client")
map_app = typer.Typer(no_args_is_help=True, help="Map configuration, tiles, and projection tools")
app.add_typer(map_app, name="map")
console = Console()
type Operation[T] = Callable[[AsyncSevenDTDClient], Awaitable[T]]


def load_cli_dotenv(env_file: Path | None = None) -> Path | None:
    """Load CLI configuration without overriding the process environment."""

    path = env_file if env_file is not None else Path.cwd() / ".env"
    if env_file is not None and not path.is_file():
        raise SevenDTDConfigurationError(f"environment file does not exist: {path}")
    if not path.is_file():
        return None
    load_dotenv(dotenv_path=path, override=False, encoding="utf-8")
    return path


@dataclass(slots=True)
class CLIState:
    base_url: str | None
    token_name: str | None
    secret: str | None
    timeout: float | None

    def settings(self) -> SevenDTDSettings:
        try:
            current = SevenDTDSettings.from_environment()
            updates: dict[str, Any] = {}
            if self.base_url is not None:
                updates["base_url"] = self.base_url
            if self.token_name is not None:
                updates["token_name"] = SecretStr(self.token_name)
            if self.secret is not None:
                updates["secret"] = SecretStr(self.secret)
            if self.timeout is not None:
                updates["timeout"] = self.timeout
            return SevenDTDSettings.model_validate({**current.model_dump(), **updates})
        except ValidationError as exc:
            raise SevenDTDConfigurationError("invalid or missing SevenDTD configuration") from exc


@app.callback()
def callback(
    ctx: typer.Context,
    base_url: Annotated[str | None, typer.Option("--base-url")] = None,
    token_name: Annotated[str | None, typer.Option("--token-name")] = None,
    secret: Annotated[str | None, typer.Option("--secret", hidden=True)] = None,
    timeout: Annotated[float | None, typer.Option("--timeout", min=0.001)] = None,
    env_file: Annotated[Path | None, typer.Option("--env-file", dir_okay=False)] = None,
    log_level: Annotated[str, typer.Option("--log-level")] = "WARNING",
    no_color: Annotated[bool, typer.Option("--no-color")] = False,
) -> None:
    del no_color
    try:
        load_cli_dotenv(env_file)
    except SevenDTDConfigurationError as exc:
        raise typer.BadParameter(str(exc), param_hint="--env-file") from exc
    logging.basicConfig(level=getattr(logging, log_level.upper(), logging.WARNING))
    ctx.obj = CLIState(base_url, token_name, secret, timeout)


def run[T](state: CLIState, operation: Operation[T]) -> T:
    async def invoke() -> T:
        async with AsyncSevenDTDClient.from_settings(state.settings()) as client:
            return await operation(client)

    try:
        return asyncio.run(invoke())
    except SevenDTDError as exc:
        emit_error(str(exc))
        raise typer.Exit(exit_code(exc)) from exc


@app.command()
def status(
    ctx: typer.Context,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    strict: Annotated[bool, typer.Option("--strict")] = False,
) -> None:
    snapshot = run(ctx.obj, lambda client: client.snapshot(strict=strict))
    if json_output:
        emit(snapshot, as_json=True)
    else:
        emit_status(snapshot)
    if not snapshot.complete:
        raise typer.Exit(6)


@app.command()
def players(
    ctx: typer.Context, json_output: Annotated[bool, typer.Option("--json")] = False
) -> None:
    emit(run(ctx.obj, lambda client: client.players.online()), as_json=json_output)


@app.command()
def hostiles(
    ctx: typer.Context, json_output: Annotated[bool, typer.Option("--json")] = False
) -> None:
    emit(run(ctx.obj, lambda client: client.entities.hostiles()), as_json=json_output)


@app.command()
def animals(
    ctx: typer.Context, json_output: Annotated[bool, typer.Option("--json")] = False
) -> None:
    emit(run(ctx.obj, lambda client: client.entities.animals()), as_json=json_output)


@app.command()
def items(
    ctx: typer.Context,
    query: Annotated[str | None, typer.Argument()] = None,
    blocks_only: Annotated[bool, typer.Option("--blocks-only")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    catalog = run(ctx.obj, lambda client: client.items.all())
    if query is not None:
        catalog = catalog.search(query, blocks_only=blocks_only)
    elif blocks_only:
        catalog = catalog.search("", blocks_only=True)
    emit(catalog, as_json=json_output)


@app.command("entity-classes")
def entity_classes(
    ctx: typer.Context,
    query: Annotated[str | None, typer.Argument()] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    if query is None:
        result = run(ctx.obj, lambda client: client.entities.classes())
    else:
        result = run(ctx.obj, lambda client: client.entities.search_classes(query))
    emit(result, as_json=json_output)


@app.command("item-search")
def item_search(
    ctx: typer.Context,
    query: str,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    try:
        prepare_search_items(query)
    except SevenDTDCommandError as exc:
        raise typer.BadParameter(str(exc), param_hint="QUERY") from exc
    emit(run(ctx.obj, lambda client: client.items.search(query)), as_json=json_output)


@app.command("entity-search")
def entity_search(
    ctx: typer.Context,
    query: str,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    emit(run(ctx.obj, lambda client: client.entities.search_classes(query)), as_json=json_output)


@app.command()
def give(
    ctx: typer.Context,
    entity_id: int,
    item_name: str,
    amount: Annotated[int, typer.Argument(min=1)],
    quality: Annotated[int | None, typer.Option("--quality", min=1, max=6)] = None,
    no_validate_item: Annotated[bool, typer.Option("--no-validate-item")] = False,
    yes: Annotated[bool, typer.Option("--yes")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    try:
        prepare_give(entity_id, item_name, amount, quality)
    except SevenDTDCommandError as exc:
        raise typer.BadParameter(str(exc), param_hint="ITEM_NAME") from exc
    if not no_validate_item:
        catalog = run(ctx.obj, lambda client: client.items.all())
        if catalog.get(item_name) is None:
            raise typer.BadParameter(
                f"item {item_name!r} is not an exact /api/item name",
                param_hint="ITEM_NAME",
            )
    quality_text = f", quality {quality}" if quality is not None else ""
    if not yes and not typer.confirm(
        f"Give entity {entity_id} item {item_name!r}, amount {amount}{quality_text}?"
    ):
        raise typer.Abort()
    result = run(
        ctx.obj,
        lambda client: client.admin.give(entity_id, item_name, amount, quality),
    )
    emit(result, as_json=json_output)


@app.command()
def say(
    ctx: typer.Context,
    message: str,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    try:
        prepare_say(message)
    except SevenDTDCommandError as exc:
        raise typer.BadParameter(str(exc), param_hint="MESSAGE") from exc
    emit(run(ctx.obj, lambda client: client.admin.say(message)), as_json=json_output)


@app.command()
def message(
    ctx: typer.Context,
    entity_id: int,
    message: str,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    try:
        prepare_message(entity_id, message)
    except SevenDTDCommandError as exc:
        raise typer.BadParameter(str(exc)) from exc
    emit(
        run(ctx.obj, lambda client: client.admin.message(entity_id, message)),
        as_json=json_output,
    )


@app.command()
def kick(
    ctx: typer.Context,
    entity_id: int,
    reason: Annotated[str | None, typer.Option("--reason")] = None,
    yes: Annotated[bool, typer.Option("--yes")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    try:
        prepare_kick(entity_id, reason)
    except SevenDTDCommandError as exc:
        raise typer.BadParameter(str(exc)) from exc
    reason_text = f", reason {reason!r}" if reason is not None else ""
    if not yes and not typer.confirm(f"Kick entity {entity_id}{reason_text}?"):
        raise typer.Abort()
    emit(
        run(ctx.obj, lambda client: client.admin.kick(entity_id, reason)),
        as_json=json_output,
    )


@app.command()
def ban(
    ctx: typer.Context,
    entity_id: int,
    duration: Annotated[int, typer.Argument(min=1)],
    unit: BanDurationUnit,
    reason: Annotated[str | None, typer.Option("--reason")] = None,
    yes: Annotated[bool, typer.Option("--yes")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    try:
        prepare_ban(entity_id, duration, unit, reason)
    except SevenDTDCommandError as exc:
        raise typer.BadParameter(str(exc)) from exc
    reason_text = f", reason {reason!r}" if reason is not None else ""
    if not yes and not typer.confirm(
        f"DESTRUCTIVE: Ban entity {entity_id} for {duration} {unit.value}{reason_text}?"
    ):
        raise typer.Abort()
    emit(
        run(ctx.obj, lambda client: client.admin.ban(entity_id, duration, unit, reason)),
        as_json=json_output,
    )


@app.command("ban-list")
def ban_list(
    ctx: typer.Context,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    prepare_ban_list()
    emit(run(ctx.obj, lambda client: client.admin.ban_list()), as_json=json_output)


@app.command()
def unban(
    ctx: typer.Context,
    combined_identity: str,
    yes: Annotated[bool, typer.Option("--yes")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    try:
        prepare_unban(combined_identity)
    except SevenDTDCommandError as exc:
        raise typer.BadParameter(str(exc), param_hint="COMBINED_IDENTITY") from exc
    if not yes and not typer.confirm(f"Remove ban for {combined_identity!r}?"):
        raise typer.Abort()
    emit(
        run(ctx.obj, lambda client: client.admin.unban(combined_identity)),
        as_json=json_output,
    )


@app.command("command")
def raw_command(
    ctx: typer.Context,
    command: str,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    yes: Annotated[bool, typer.Option("--yes")] = False,
) -> None:
    if not yes and not typer.confirm("Execute arbitrary server command?"):
        raise typer.Abort()
    emit(run(ctx.obj, lambda client: client.commands.execute(command)), as_json=json_output)


@app.command("console")
def console_command(ctx: typer.Context) -> None:
    if not typer.confirm("Open arbitrary administrative console?"):
        raise typer.Abort()
    while True:
        try:
            command = typer.prompt("7dtd", prompt_suffix="> ")
        except (EOFError, KeyboardInterrupt):
            raise typer.Exit(130) from None
        if command.strip().lower() in {"exit", "quit"}:
            return

        async def execute(
            client: AsyncSevenDTDClient, current_command: str = command
        ) -> CommandResult:
            return await client.commands.execute(current_command)

        emit(run(ctx.obj, execute), as_json=False)


@app.command()
def logs(
    ctx: typer.Context,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    no_reconnect: Annotated[bool, typer.Option("--no-reconnect")] = False,
    max_retries: Annotated[int | None, typer.Option("--max-retries", min=0)] = None,
) -> None:
    async def follow() -> None:
        policy = None if no_reconnect else ReconnectPolicy(max_attempts=max_retries)
        async with AsyncSevenDTDClient.from_settings(ctx.obj.settings()) as client:
            async for event in client.logs.stream(reconnect=policy):
                if json_output:
                    emit_json_line(event)
                elif isinstance(event, LogLineEvent):
                    console.print(event.payload.msg)
                else:
                    console.print(event.raw_data)

    try:
        asyncio.run(follow())
    except KeyboardInterrupt:
        raise typer.Exit(130) from None
    except SevenDTDError as exc:
        emit_error(str(exc))
        raise typer.Exit(exit_code(exc)) from exc


@map_app.command("info")
def map_info(
    ctx: typer.Context, json_output: Annotated[bool, typer.Option("--json")] = False
) -> None:
    emit(run(ctx.obj, lambda client: client.map.config()), as_json=json_output)


@map_app.command("tile")
def map_tile(
    ctx: typer.Context,
    zoom: Annotated[int, typer.Option("--zoom", min=0)],
    coord_a: Annotated[int, typer.Option("--coord-a")],
    coord_b: Annotated[int, typer.Option("--coord-b")],
    output: Annotated[Path, typer.Option("--output")],
    cache_token: Annotated[str | None, typer.Option("--cache-token")] = None,
    force: Annotated[bool, typer.Option("--force")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    if output.exists() and not force:
        raise typer.BadParameter("output exists; pass --force to replace it")
    tile = run(
        ctx.obj,
        lambda client: client.map.tile(
            zoom=zoom, coord_a=coord_a, coord_b=coord_b, cache_token=cache_token
        ),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(tile.content)
    try:
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    emit(
        {
            "coordinate": tile.coordinate.model_dump(),
            "content_length": tile.content_length,
            "path": str(output),
        },
        as_json=json_output,
    )


@map_app.command("locate")
def map_locate(
    ctx: typer.Context,
    x: Annotated[float, typer.Option("--x")],
    z: Annotated[float, typer.Option("--z")],
    zoom: Annotated[int, typer.Option("--zoom", min=0, max=4)],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    async def locate(client: AsyncSevenDTDClient) -> dict[str, object]:
        projection = await client.map.projection()
        position = WorldHorizontalPosition(x=x, z=z)
        tile = projection.world_to_tile(position, zoom)
        bounds = projection.tile_to_world_bounds(tile)
        return {
            "position": position.model_dump(),
            "tile": asdict(tile),
            "span": projection.span_for_zoom(zoom),
            "bounds": asdict(bounds),
            "evidence_identifier": projection.spec.evidence_identifier,
        }

    emit(run(ctx.obj, locate), as_json=json_output)


@map_app.command("mosaic")
def map_mosaic(
    ctx: typer.Context,
    zoom: Annotated[int, typer.Option("--zoom", min=0)],
    a_start: Annotated[int, typer.Option("--a-start")],
    a_end: Annotated[int, typer.Option("--a-end")],
    b_start: Annotated[int, typer.Option("--b-start")],
    b_end: Annotated[int, typer.Option("--b-end")],
    output: Annotated[Path, typer.Option("--output")],
    manifest: Annotated[Path, typer.Option("--manifest")],
    annotate: Annotated[bool, typer.Option("--annotate")] = False,
    cache_token: Annotated[str | None, typer.Option("--cache-token")] = None,
    concurrency: Annotated[int, typer.Option("--concurrency", min=1, max=64)] = 8,
    force: Annotated[bool, typer.Option("--force")] = False,
    allow_large_grid: Annotated[bool, typer.Option("--allow-large-grid")] = False,
) -> None:
    if (output.exists() or manifest.exists()) and not force:
        raise typer.BadParameter("output or manifest exists; pass --force to replace")
    a_values, b_values = inclusive_range(a_start, a_end), inclusive_range(b_start, b_end)
    if len(a_values) * len(b_values) > 1024 and not allow_large_grid:
        raise typer.BadParameter("grid exceeds 1024 tiles; pass --allow-large-grid")

    async def create(client: AsyncSevenDTDClient) -> dict[str, object]:
        return await create_mosaic(
            client,
            zoom=zoom,
            a_values=a_values,
            b_values=b_values,
            output=output,
            manifest=manifest,
            annotate=annotate,
            cache_token=cache_token,
            concurrency=concurrency,
        )

    document = run(ctx.obj, create)
    entries = document.get("entries")
    tile_count = len(cast(list[object], entries)) if isinstance(entries, list) else 0
    console.print(f"Wrote {output} and {manifest} ({tile_count} tiles)")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
