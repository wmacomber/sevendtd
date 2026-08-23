import asyncio
import json
from pathlib import Path

import httpx
import pytest
from pydantic import SecretStr

from sevendtd.client import AsyncSevenDTDClient
from sevendtd.exceptions import SevenDTDAPIError, SevenDTDAuthenticationError
from sevendtd.transport.http import HTTPTransport

FIXTURES = Path(__file__).parents[1] / "fixtures"


def client() -> AsyncSevenDTDClient:
    async def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(500)

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return AsyncSevenDTDClient(
        HTTPTransport(
            base_url="http://example.test",
            token_name=SecretStr("token"),
            secret=SecretStr("secret"),
            client=http_client,
            owns_client=True,
        )
    )


@pytest.mark.asyncio
async def test_snapshot_returns_safe_partial_failures() -> None:
    instance = client()
    snapshot = await instance.snapshot()
    assert not snapshot.complete
    assert {failure.component for failure in snapshot.failures} == {
        "server_info",
        "server_stats",
        "online_players",
        "hostiles",
        "animals",
        "map_config",
    }
    assert all("HTTP 500" in failure.message for failure in snapshot.failures)
    await instance.close()


@pytest.mark.asyncio
async def test_strict_snapshot_raises_aggregate_error() -> None:
    from sevendtd.exceptions import SevenDTDSnapshotError

    instance = client()
    with pytest.raises(SevenDTDSnapshotError) as captured:
        await instance.snapshot(strict=True)
    assert len(captured.value.failures) == 6
    await instance.close()


@pytest.mark.asyncio
async def test_strict_snapshot_waits_for_all_concurrent_failures() -> None:
    from sevendtd.exceptions import SevenDTDSnapshotError

    instance = client()
    completed: list[str] = []

    async def fail(name: str, turns: int) -> None:
        for _ in range(turns):
            await asyncio.sleep(0)
        completed.append(name)
        raise SevenDTDAPIError(f"/api/{name}", 500)

    instance.server.info = lambda: fail("server_info", 5)  # type: ignore[method-assign]
    instance.server.stats = lambda: fail("server_stats", 4)  # type: ignore[method-assign]
    instance.players.online = lambda: fail("online_players", 3)  # type: ignore[method-assign]
    instance.entities.hostiles = lambda: fail("hostiles", 2)  # type: ignore[method-assign]
    instance.entities.animals = lambda: fail("animals", 1)  # type: ignore[method-assign]
    instance.map.config = lambda: fail("map_config", 0)  # type: ignore[method-assign]
    with pytest.raises(SevenDTDSnapshotError) as captured:
        await instance.snapshot(strict=True)
    assert len(captured.value.failures) == 6
    assert set(completed) == {
        "server_info",
        "server_stats",
        "online_players",
        "hostiles",
        "animals",
        "map_config",
    }
    await instance.close()


@pytest.mark.asyncio
async def test_authentication_failure_is_not_converted_to_partial_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    instance = client()

    async def authenticate() -> None:
        raise SevenDTDAuthenticationError("/api/serverinfo", 401)

    async def ordinary_failure() -> None:
        raise SevenDTDAPIError("/api/other", 500)

    monkeypatch.setattr(instance.server, "info", authenticate)
    monkeypatch.setattr(instance.server, "stats", ordinary_failure)
    monkeypatch.setattr(instance.players, "online", ordinary_failure)
    monkeypatch.setattr(instance.entities, "hostiles", ordinary_failure)
    monkeypatch.setattr(instance.entities, "animals", ordinary_failure)
    monkeypatch.setattr(instance.map, "config", ordinary_failure)
    with pytest.raises(SevenDTDAuthenticationError):
        await instance.snapshot()
    await instance.close()


@pytest.mark.asyncio
async def test_snapshot_executes_all_components_concurrently() -> None:
    fixture_by_path = {
        "/api/serverinfo": "serverinfo.json",
        "/api/serverstats": "serverstats.json",
        "/api/player": "players.json",
        "/api/hostile": "hostiles.json",
        "/api/animal": "animals-empty.json",
        "/api/map/config": "map-config.json",
    }
    active = 0
    maximum_active = 0
    release = asyncio.Event()

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal active, maximum_active
        active += 1
        maximum_active = max(maximum_active, active)
        if active == len(fixture_by_path):
            release.set()
        await asyncio.wait_for(release.wait(), timeout=1)
        active -= 1
        return httpx.Response(
            200, json=json.loads((FIXTURES / fixture_by_path[request.url.path]).read_text())
        )

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    instance = AsyncSevenDTDClient(
        HTTPTransport(
            base_url="http://example.test",
            token_name=SecretStr("token"),
            secret=SecretStr("secret"),
            client=http_client,
            owns_client=True,
        )
    )
    snapshot = await instance.snapshot()
    assert snapshot.complete
    assert snapshot.server_info is not None
    assert snapshot.map_config is not None
    assert maximum_active == 6
    await instance.close()


@pytest.mark.asyncio
async def test_partial_snapshot_preserves_successful_components() -> None:
    instance = client()

    async def successful_info() -> object:
        fixture = json.loads((FIXTURES / "serverinfo.json").read_text())
        response = httpx.Response(200, json=fixture)

        async def handler(_request: httpx.Request) -> httpx.Response:
            return response

        owned = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        transport = HTTPTransport(
            base_url="http://example.test",
            token_name=SecretStr("token"),
            secret=SecretStr("secret"),
            client=owned,
            owns_client=True,
        )
        try:
            return await type(instance.server)(transport).info()
        finally:
            await transport.close()

    instance.server.info = successful_info  # type: ignore[method-assign]
    snapshot = await instance.snapshot()
    assert snapshot.server_info is not None
    assert {failure.component for failure in snapshot.failures} == {
        "server_stats",
        "online_players",
        "hostiles",
        "animals",
        "map_config",
    }
    await instance.close()


@pytest.mark.asyncio
async def test_authentication_failure_cancels_pending_components() -> None:
    instance = client()
    started = 0
    all_started = asyncio.Event()
    cancelled: list[str] = []

    async def wait_for_cancellation(name: str) -> None:
        nonlocal started
        started += 1
        if started == 5:
            all_started.set()
        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            cancelled.append(name)
            raise

    async def authenticate() -> None:
        await all_started.wait()
        raise SevenDTDAuthenticationError("/api/serverinfo", 401)

    instance.server.info = authenticate  # type: ignore[method-assign]
    instance.server.stats = lambda: wait_for_cancellation("server_stats")  # type: ignore[method-assign]
    instance.players.online = lambda: wait_for_cancellation("online_players")  # type: ignore[method-assign]
    instance.entities.hostiles = lambda: wait_for_cancellation("hostiles")  # type: ignore[method-assign]
    instance.entities.animals = lambda: wait_for_cancellation("animals")  # type: ignore[method-assign]
    instance.map.config = lambda: wait_for_cancellation("map_config")  # type: ignore[method-assign]
    with pytest.raises(SevenDTDAuthenticationError):
        await instance.snapshot()
    assert set(cancelled) == {
        "server_stats",
        "online_players",
        "hostiles",
        "animals",
        "map_config",
    }
    await instance.close()


@pytest.mark.asyncio
async def test_unexpected_snapshot_failure_message_is_sanitized() -> None:
    instance = client()

    async def unsafe_failure() -> None:
        raise RuntimeError("credential distinct-secret must not escape")

    instance.server.info = unsafe_failure  # type: ignore[method-assign]
    instance.server.stats = unsafe_failure  # type: ignore[method-assign]
    instance.players.online = unsafe_failure  # type: ignore[method-assign]
    instance.entities.hostiles = unsafe_failure  # type: ignore[method-assign]
    instance.entities.animals = unsafe_failure  # type: ignore[method-assign]
    instance.map.config = unsafe_failure  # type: ignore[method-assign]
    snapshot = await instance.snapshot()
    assert all("distinct-secret" not in failure.message for failure in snapshot.failures)
    assert {failure.message for failure in snapshot.failures} == {
        "server_info failed",
        "server_stats failed",
        "online_players failed",
        "hostiles failed",
        "animals failed",
        "map_config failed",
    }
    await instance.close()
