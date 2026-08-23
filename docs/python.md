# Python consumer guide

`sevendtd` is an async Python client for the 7 Days to Die dedicated-server web API. It exposes
typed resource namespaces, preserves upstream observation times, and keeps authentication inside
the transport layer.

This guide targets application developers. Protocol evidence lives in
[upstream-api.md](upstream-api.md); architectural decisions live in
[architecture.md](architecture.md).

## Installation

Python 3.12 or newer is required. The project is currently versioned `0.4.0.dev0` and this guide
does not claim a published package index release.

From a source checkout, create the project environment:

```bash
uv sync --all-extras --dev
```

To consume a locally built wheel from another project:

```bash
uv build
uv add /path/to/sevendtd/dist/sevendtd-0.4.0.dev0-py3-none-any.whl
```

The core client uses HTTPX and Pydantic. Python-dotenv supports CLI configuration. Typer, Rich, and
Pillow belong to optional CLI/image tooling and are not imported by the core client.

## Configuration

Environment-backed configuration uses these exact names:

```dotenv
SEVENTDTD_BASE_URL=http://server.example:26980
SEVENTDTD_TOKEN_NAME=replace-me
SEVENTDTD_SECRET=replace-me
SEVENTDTD_TIMEOUT=10
```

Load them explicitly:

```python
from sevendtd import SevenDTDSettings

settings = SevenDTDSettings.from_environment()
```

Embedded applications and tests can provide values directly:

```python
from sevendtd import SevenDTDSettings

settings = SevenDTDSettings.from_values(
    base_url="http://server.example:26980",
    token_name="replace-me",
    secret="replace-me",
    timeout=10.0,
)
```

Credentials have no defaults. `SecretStr` masks them in normal representations. Do not serialize
settings into application state or send game-server credentials to browsers. See
[configuration.md](configuration.md) for CLI `.env` behavior and logging safeguards.

## Client lifecycle

Create one client for the application lifetime. Async context exit closes a client created by
`AsyncSevenDTDClient.from_settings()`.

```python
import asyncio

from sevendtd import AsyncSevenDTDClient, SevenDTDSettings


async def main() -> None:
    settings = SevenDTDSettings.from_environment()
    async with AsyncSevenDTDClient.from_settings(settings) as client:
        info = await client.server.info()
        print(info.game_name, info.observed_at)


if __name__ == "__main__":
    asyncio.run(main())
```

An injected `httpx.AsyncClient` remains caller-owned unless `owns_http_client=True` is supplied:

```python
import httpx

from sevendtd import AsyncSevenDTDClient, SevenDTDSettings


async def use_shared_http_client(settings: SevenDTDSettings) -> None:
    http_client = httpx.AsyncClient()
    try:
        async with AsyncSevenDTDClient.from_settings(
            settings,
            http_client=http_client,
        ) as client:
            await client.server.stats()
    finally:
        await http_client.aclose()
```

## Resource namespaces

| Namespace | Operation | Result |
|---|---|---|
| `client.server` | `info()` | `ServerInfo` property bag and typed accessors |
| `client.server` | `stats()` | `ServerStats` |
| `client.players` | `online()` | `OnlinePlayers` |
| `client.entities` | `hostiles()`, `animals()` | Entity collections |
| `client.entities` | `classes()`, `search_classes(query)` | Entity-class catalogs |
| `client.items` | `all()`, `search(query)` | Typed catalog or server-side name search |
| `client.commands` | `execute(command)` | Raw `CommandResult` |
| `client.logs` | `stream(reconnect=...)` | Async SSE event stream |
| `client.map` | `config()`, `tile(...)`, `projection()` | Map configuration, PNG bytes, projection |
| `client.admin` | prepare and execute helpers | Risk-labelled typed console commands |
| root client | `snapshot(strict=False)` | Concurrent current-state snapshot |

### Server, players, and entities

```python
from sevendtd import AsyncSevenDTDClient


async def read_current_state(client: AsyncSevenDTDClient) -> None:
    info = await client.server.info()
    stats = await client.server.stats()
    online = await client.players.online()
    hostiles = await client.entities.hostiles()
    animals = await client.entities.animals()

    print(info.game_name, info.server_version, info.max_players)
    print(stats.game_time.days, stats.players)
    for player in online.players:
        print(player.entity_id, player.name, player.position.x, player.position.z)
    for hostile in hostiles.items:
        print(hostile.id, hostile.name, hostile.position)
    for animal in animals.items:
        print(animal.root)
```

`ServerInfo` preserves the ordered upstream property bag. `get(name)` returns the last matching
value; `get_all(name)` retains duplicates. Animals remain opaque mappings because no stable non-empty
schema has been observed.

### Item and entity-class catalogs

`items.all()` downloads typed metadata. `items.search()` invokes the verified server-side `li`
command and returns internal names only.

```python
from sevendtd import AsyncSevenDTDClient


async def search_catalogs(client: AsyncSevenDTDClient) -> None:
    catalog = await client.items.all()
    exact = catalog.get("resourceWood")
    local_matches = catalog.search("wood", blocks_only=False)
    server_matches = await client.items.search("resourceWood")

    classes = await client.entities.classes()
    zombie_classes = classes.search("zombie")

    print(exact, local_matches.items, server_matches.names, zombie_classes.items)
```

Catalog lookup by internal item name is case-sensitive. Local searches are case-insensitive and can
use localized names. Server-side item-search queries use a conservative single-token grammar.

## Model conventions

- Public resource aggregates expose upstream `meta.serverTime` as `observed_at`.
- Datetimes are timezone-aware.
- World coordinates are floats.
- `model_dump()` emits Python-facing snake case by default.
- `model_dump(by_alias=True)` emits captured upstream aliases where defined.
- Unknown response fields remain in Pydantic `model_extra` and survive serialization.
- Fields observed as nullable remain nullable.
- Player IP values are plain strings. Applications decide whether and how to parse them.

Observation time describes upstream state, not local receipt time. Applications needing latency or
staleness should record their own collection timestamp beside `observed_at`.

```python
from sevendtd import Player


def serialize_player(player: Player) -> dict[str, object]:
    python_shape = player.model_dump()
    upstream_shape = player.model_dump(by_alias=True)
    return {"python": python_shape, "upstream": upstream_shape}
```

## Snapshots

`snapshot()` requests server information, statistics, players, hostiles, animals, and map
configuration concurrently. Default mode preserves successes when ordinary components fail.

```python
from sevendtd import AsyncSevenDTDClient


async def inspect_snapshot(client: AsyncSevenDTDClient) -> None:
    snapshot = await client.snapshot()
    if snapshot.online_players is not None:
        print(snapshot.online_players.players)
    if not snapshot.complete:
        for failure in snapshot.failures:
            print(failure.component, failure.error_type, failure.message)
```

`snapshot(strict=True)` waits for concurrent components, then raises `SevenDTDSnapshotError` with
all ordinary failures. Authentication failure remains immediate. Catalogs are intentionally absent
because they are large, mostly static definitions rather than current server state.

## Log streaming

Without a reconnect policy, `stream()` opens one connection. Explicit policy enables capped or
unbounded reconnect behavior.

```python
from sevendtd import (
    AsyncSevenDTDClient,
    LogLineEvent,
    MalformedLogEvent,
    ReconnectPolicy,
    UnknownLogEvent,
)


async def follow_logs(client: AsyncSevenDTDClient) -> None:
    policy = ReconnectPolicy(max_attempts=None)
    async for event in client.logs.stream(reconnect=policy):
        if isinstance(event, LogLineEvent):
            print(event.payload.isotime, event.payload.msg)
        elif isinstance(event, MalformedLogEvent):
            print("Malformed:", event.error)
        elif isinstance(event, UnknownLogEvent):
            print("Unknown:", event.event_type, event.raw_data)
```

Unknown and malformed events stay observable. Cancellation propagates during reads and reconnect
backoff. Authentication and non-transient client errors are not retried. Log SSE does not provide a
player-position stream; live maps must poll `players.online()`.

## Map projection and tiles

`client.map.projection()` fetches live configuration and returns the verified transform only when
`mapBlockSize == 128` and `maxZoom == 4`. Other configurations raise `SevenDTDMapTileError`; raw
tile access remains available.

```python
from pathlib import Path

from sevendtd import AsyncSevenDTDClient, WorldHorizontalPosition


async def save_player_tile(client: AsyncSevenDTDClient) -> None:
    online = await client.players.online()
    if not online.players:
        return

    player = online.players[0]
    position = WorldHorizontalPosition(x=player.position.x, z=player.position.z)
    projection = await client.map.projection()
    coordinate = projection.world_to_tile(position, zoom=4)
    bounds = projection.tile_to_world_bounds(coordinate)

    assert projection.contains(coordinate, position)
    tile = await client.map.tile(
        zoom=coordinate.zoom,
        coord_a=coordinate.coord_a,
        coord_b=coordinate.coord_b,
    )
    Path("player-tile.png").write_bytes(tile.content)
    print(coordinate, projection.span_for_zoom(4), bounds)
```

Native tile spans are 2048, 1024, 512, 256, and 128 world units for zooms 0–4. X bounds use
`[min_x, max_x)`; Z bounds use `(min_z, max_z]`. `cache_token` is opaque and passed as query
parameter `t` without interpretation.

Core tile retrieval validates non-empty PNG bytes and reported media type. It does not decode image
pixels. `world_to_tile_pixel()` is deliberately unavailable because pixel orientation and rounding
remain unverified. See [map-projection.md](map-projection.md) for evidence and limitations.

## Framework-neutral live-map collector

Use one server-side collector and fan out its sanitized state. Do not create one game-server poller
per browser.

```text
game server -> sevendtd collector -> sanitized state + tile cache -> browsers
                 credentials              no credentials
```

The application chooses its polling interval after measuring server load and desired freshness.
This complete example accepts that interval rather than prescribing one:

```python
import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from sevendtd import (
    AsyncSevenDTDClient,
    SevenDTDAuthenticationError,
    SevenDTDConnectionError,
    SevenDTDSettings,
    SevenDTDTimeoutError,
    WorldHorizontalPosition,
)

SafeState = dict[str, object]
Publish = Callable[[SafeState], Awaitable[None]]


async def run_live_map_collector(
    settings: SevenDTDSettings,
    *,
    poll_interval: float,
    retry_delay: float,
    publish: Publish,
) -> None:
    if poll_interval <= 0 or retry_delay < 0:
        raise ValueError("poll_interval must be positive and retry_delay non-negative")

    async with AsyncSevenDTDClient.from_settings(settings) as client:
        projection = await client.map.projection()
        last_good: SafeState | None = None

        while True:
            try:
                online = await client.players.online()
            except SevenDTDAuthenticationError:
                raise
            except (SevenDTDConnectionError, SevenDTDTimeoutError) as exc:
                if last_good is not None:
                    await publish(
                        {
                            **last_good,
                            "stale": True,
                            "error_type": type(exc).__name__,
                        }
                    )
                await asyncio.sleep(retry_delay)
                continue

            players: list[dict[str, object]] = []
            for player in online.players:
                horizontal = WorldHorizontalPosition(
                    x=player.position.x,
                    z=player.position.z,
                )
                tile = projection.world_to_tile(horizontal, zoom=4)
                players.append(
                    {
                        "entity_id": player.entity_id,
                        "display_name": player.name,
                        "position": {
                            "x": player.position.x,
                            "y": player.position.y,
                            "z": player.position.z,
                        },
                        "tile": {
                            "zoom": tile.zoom,
                            "coord_a": tile.coord_a,
                            "coord_b": tile.coord_b,
                        },
                    }
                )

            state: SafeState = {
                "upstream_observed_at": online.observed_at.isoformat(),
                "collected_at": datetime.now(UTC).isoformat(),
                "stale": False,
                "players": players,
            }
            last_good = state
            await publish(state)
            await asyncio.sleep(poll_interval)
```

The manual dictionary is the privacy boundary. It excludes IP addresses, platform identities,
cross-platform identities, health, and unrelated player fields. Display names and positions remain
sensitive even on a trusted LAN; expose them intentionally.

`publish` can update in-memory state, a queue, WebSocket broadcaster, Server-Sent Events endpoint,
or another application-owned channel. A database is unnecessary for current live state unless the
application needs history.

The web application should expose its own tile endpoint backed by `client.map.tile()` and a bounded
cache. Browser code calls that endpoint, never the game server. Cache keys should include zoom,
`coord_a`, `coord_b`, and any application freshness policy. The library does not yet define cache
token semantics.

On transient failure, mark the last successful state stale instead of silently presenting it as
current. Authentication failure should stop the collector and alert the operator. After a game
server restart, world change, or map-configuration change, recreate the projection by restarting or
reinitializing the collector. Normal task cancellation needs no special wrapper; `CancelledError`
propagates through library operations and `asyncio.sleep()`.

This pattern assumes trusted LAN viewers. Internet exposure additionally requires application
authentication, TLS, stricter identity minimization, request and connection limits, tile-cache
limits, and explicit operator review. The game API must remain unreachable from browser clients.

## Commands and administration

Prefer typed administrative helpers. Preparation exposes risk before execution and never contacts
the server.

```python
from sevendtd import AsyncSevenDTDClient, BanDurationUnit


async def prepare_administration(client: AsyncSevenDTDClient) -> None:
    message = client.admin.prepare_say("Server restart in ten minutes")
    gift = client.admin.prepare_give(171, "resourceWood", 2)
    ban = client.admin.prepare_ban(
        171,
        1,
        BanDurationUnit.MINUTE,
        "CLI moderation test",
    )

    print(message.metadata.risk, gift.metadata.risk, ban.metadata.risk)
    await client.admin.execute(message)
```

Convenience methods such as `say()`, `message()`, `give()`, `kick()`, `ban()`, `ban_list()`, and
`unban()` use the same prepared-command path. `get_time()`, `save_world()`, and `shutdown()` are also
available. Captured generic help proves those three command names exist, but command-specific help
was unavailable; their metadata therefore reports `syntax_verified=False` and describes the
catalog evidence in `verification_evidence`. Their raw commands and risk classifications remain
unchanged. Risk metadata is advisory; upstream permissions authorize execution.

`client.commands.execute()` remains the raw escape hatch. It rejects empty values and NUL/CR/LF but
does not make arbitrary commands safe. Do not accept raw browser input and forward it to the game
console.

## Errors and retry policy

Project exception hierarchy:

```text
SevenDTDError
├── SevenDTDConfigurationError
├── SevenDTDTransportError
│   ├── SevenDTDConnectionError
│   └── SevenDTDTimeoutError
├── SevenDTDAuthenticationError
├── SevenDTDAPIError
├── SevenDTDInvalidResponseError
├── SevenDTDCommandError
├── SevenDTDSSEError
├── SevenDTDMapTileError
└── SevenDTDSnapshotError
```

All operational library exceptions derive from `SevenDTDError`:

| Exception | Meaning | Typical application action |
|---|---|---|
| `SevenDTDConfigurationError` | Project-normalized configuration failure | Correct settings before creating client |
| `SevenDTDAuthenticationError` | HTTP 401/403 | Stop; fix credentials or permissions |
| `SevenDTDConnectionError` | Network failure | Mark stale; retry with application backoff |
| `SevenDTDTimeoutError` | Finite operation timed out | Mark stale; retry if operation is safe |
| `SevenDTDAPIError` | Other unsuccessful HTTP status | Inspect safe endpoint/status; classify before retry |
| `SevenDTDInvalidResponseError` | JSON/model mismatch | Stop automatic retry loop; investigate protocol drift |
| `SevenDTDCommandError` | Invalid command input/result | Correct input or inspect upstream change |
| `SevenDTDSSEError` | Stream/reconnect failure | Reconnect only under explicit policy |
| `SevenDTDMapTileError` | Invalid tile or unsupported projection | Fall back to raw coordinates or reject feature |
| `SevenDTDSnapshotError` | Strict snapshot component failures | Inspect aggregated failures |

Direct settings validation uses Pydantic validation errors before transport creation. Authentication
is never retried by the library. Finite HTTP resources do not retry automatically; applications own
retry timing and should retry only idempotent/read-only operations unless command semantics prove
otherwise.

```python
from sevendtd import (
    AsyncSevenDTDClient,
    SevenDTDAuthenticationError,
    SevenDTDConnectionError,
    SevenDTDSettings,
    SevenDTDTimeoutError,
)


async def guarded_read(settings: SevenDTDSettings) -> None:
    try:
        async with AsyncSevenDTDClient.from_settings(settings) as client:
            await client.players.online()
    except SevenDTDAuthenticationError:
        raise
    except (SevenDTDConnectionError, SevenDTDTimeoutError):
        print("Server temporarily unavailable")
```

## Testing consumers

Inject a caller-owned `httpx.AsyncClient` with `httpx.MockTransport` or use a higher-level fake at
the namespace boundary. Never require a live game server for normal application tests. Verify that
sanitized web state excludes credentials, IPs, and platform identities. Verify stale-state behavior,
collector cancellation, unsupported map configuration, and multiple viewers sharing one poller.

Repository test gates and commands are documented in [testing.md](testing.md). CLI behavior is
documented separately in [cli.md](cli.md).
