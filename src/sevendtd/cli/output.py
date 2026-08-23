"""CLI serialization and compact human rendering."""

import json
from typing import Any

import typer
from pydantic import BaseModel
from pydantic_core import to_jsonable_python
from rich.console import Console
from rich.pretty import Pretty
from rich.table import Table

from sevendtd.models.snapshot import ServerSnapshot

stdout = Console()
stderr = Console(stderr=True)


def json_text(value: Any) -> str:
    if isinstance(value, BaseModel):
        return value.model_dump_json()
    return json.dumps(to_jsonable_python(value), separators=(",", ":"))


def emit(value: Any, *, as_json: bool) -> None:
    if as_json:
        emit_json_line(value)
    else:
        stdout.print(Pretty(value.model_dump() if isinstance(value, BaseModel) else value))


def emit_json_line(value: Any) -> None:
    """Write one exact, unwrapped JSON document to stdout."""

    typer.echo(json_text(value))


def emit_status(snapshot: ServerSnapshot) -> None:
    """Render snapshot successes and failures without hiding partial state."""

    failures = {failure.component: failure for failure in snapshot.failures}
    table = Table(title="Server status")
    table.add_column("Component")
    table.add_column("State")
    table.add_column("Details", overflow="fold")
    for component in (
        "server_info",
        "server_stats",
        "online_players",
        "hostiles",
        "animals",
        "map_config",
    ):
        value = getattr(snapshot, component)
        if value is not None:
            current: Any = value
            if component == "server_info":
                details = (
                    f"game={current.game_name or 'unknown'}, "
                    f"version={current.server_version or 'unknown'}"
                )
            elif component == "server_stats":
                details = (
                    f"players={current.players}, hostiles={current.hostiles}, "
                    f"animals={current.animals}"
                )
            elif component == "online_players":
                details = f"{len(current.players)} online"
            elif component in {"hostiles", "animals"}:
                details = f"{len(current.items)} observed"
            else:
                details = f"tile={current.map_block_size}px, max_zoom={current.max_zoom}"
            table.add_row(component, "ok", details, style="green")
            continue
        failure = failures.get(component)
        if failure is None:
            table.add_row(component, "missing", "no result", style="yellow")
        else:
            table.add_row(
                component,
                "failed",
                f"{failure.error_type}: {failure.message}",
                style="red",
            )
    stdout.print(table)


def emit_error(message: str) -> None:
    stderr.print(message, markup=False, highlight=False)
