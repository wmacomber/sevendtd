import json
import logging
from pathlib import Path

import httpx
import pytest
from pydantic import SecretStr

from sevendtd.admin.metadata import BanDurationUnit
from sevendtd.admin.namespace import AdminNamespace
from sevendtd.client import AsyncSevenDTDClient
from sevendtd.config import SevenDTDSettings
from sevendtd.exceptions import (
    SevenDTDAuthenticationError,
    SevenDTDCommandError,
    SevenDTDMapTileError,
)
from sevendtd.resources.commands import CommandsNamespace, validate_command
from sevendtd.resources.entities import EntitiesNamespace
from sevendtd.resources.items import ItemsNamespace
from sevendtd.resources.map import MapNamespace
from sevendtd.resources.server import ServerNamespace
from sevendtd.transport.http import SECRET_HEADER, TOKEN_HEADER, HTTPTransport

FIXTURES = Path(__file__).parents[1] / "fixtures"


@pytest.mark.asyncio
async def test_injected_client_uses_configured_url_and_auth(
    caplog: pytest.LogCaptureFixture,
) -> None:
    observed: httpx.Request | None = None

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal observed
        observed = request
        return httpx.Response(200, json=json.loads((FIXTURES / "serverinfo.json").read_text()))

    secret = "distinct-secret-never-log"
    token = "distinct-token-never-log"
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    transport = HTTPTransport(
        base_url="http://configured.example:26980",
        token_name=SecretStr(token),
        secret=SecretStr(secret),
        client=client,
    )
    with caplog.at_level(logging.INFO, logger="sevendtd"):
        info = await ServerNamespace(transport).info()
    assert info.max_players == 8
    assert observed is not None
    assert str(observed.url) == "http://configured.example:26980/api/serverinfo"
    assert observed.headers[TOKEN_HEADER] == token
    assert observed.headers[SECRET_HEADER] == secret
    combined_logs = " ".join(record.getMessage() for record in caplog.records)
    assert secret not in combined_logs
    assert token not in combined_logs
    await client.aclose()


@pytest.mark.asyncio
async def test_caller_owned_http_client_remains_open_by_default() -> None:
    http_client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _request: httpx.Response(200))
    )
    instance = AsyncSevenDTDClient.from_settings(
        SevenDTDSettings.from_values(
            base_url="http://configured.example", token_name="token", secret="secret"
        ),
        http_client=http_client,
    )
    await instance.close()
    assert not http_client.is_closed
    await http_client.aclose()


@pytest.mark.asyncio
async def test_explicitly_transferred_http_client_is_closed() -> None:
    http_client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _request: httpx.Response(200))
    )
    instance = AsyncSevenDTDClient.from_settings(
        SevenDTDSettings.from_values(
            base_url="http://configured.example", token_name="token", secret="secret"
        ),
        http_client=http_client,
        owns_http_client=True,
    )
    await instance.close()
    assert http_client.is_closed


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("content", "content_type", "message"),
    [
        (b"", "image/png", "empty tile"),
        (b"not-png", "image/png", "invalid PNG"),
        (b"\x89PNG\r\n\x1a\nbytes", "text/plain", "content type"),
    ],
)
async def test_map_tile_rejects_invalid_transport_responses(
    content: bytes, content_type: str, message: str
) -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=content, headers={"content-type": content_type})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    transport = HTTPTransport(
        base_url="http://configured.example",
        token_name=SecretStr("token"),
        secret=SecretStr("secret"),
        client=client,
    )
    with pytest.raises(SevenDTDMapTileError, match=message):
        await MapNamespace(transport).tile(zoom=1, coord_a=2, coord_b=3)
    await client.aclose()


@pytest.mark.asyncio
async def test_map_tile_retains_valid_response_metadata() -> None:
    content = b"\x89PNG\r\n\x1a\nbytes"

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["t"] == "opaque-cache-token"
        return httpx.Response(
            200,
            content=content,
            headers={
                "content-type": "image/png",
                "etag": '"abc"',
                "last-modified": "Sun, 23 Aug 2026 12:00:00 GMT",
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    transport = HTTPTransport(
        base_url="http://configured.example",
        token_name=SecretStr("token"),
        secret=SecretStr("secret"),
        client=client,
    )
    tile = await MapNamespace(transport).tile(
        zoom=1, coord_a=2, coord_b=3, cache_token="opaque-cache-token"
    )
    assert tile.coordinate.model_dump() == {"zoom": 1, "coord_a": 2, "coord_b": 3}
    assert tile.content_length == len(content)
    assert tile.etag == '"abc"'
    assert tile.last_modified == "Sun, 23 Aug 2026 12:00:00 GMT"
    await client.aclose()


@pytest.mark.asyncio
async def test_auth_status_translates_without_response_body() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(401, text="sensitive upstream body")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    transport = HTTPTransport(
        base_url="http://configured.example",
        token_name=SecretStr("token"),
        secret=SecretStr("secret"),
        client=client,
    )
    with pytest.raises(SevenDTDAuthenticationError) as captured:
        await ServerNamespace(transport).info()
    assert "sensitive upstream body" not in str(captured.value)
    await client.aclose()


@pytest.mark.parametrize("command", ["", "   ", "say x\nshutdown", "x\r", "x\x00"])
def test_raw_command_rejects_empty_and_control_characters(command: str) -> None:
    with pytest.raises(SevenDTDCommandError):
        validate_command(command)


@pytest.mark.asyncio
async def test_command_body_is_exact_and_log_omits_text(caplog: pytest.LogCaptureFixture) -> None:
    observed: httpx.Request | None = None

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal observed
        observed = request
        return httpx.Response(200, json=json.loads((FIXTURES / "command-help.json").read_text()))

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    transport = HTTPTransport(
        base_url="http://configured.example",
        token_name=SecretStr("token"),
        secret=SecretStr("secret"),
        client=client,
    )
    with caplog.at_level(logging.INFO, logger="sevendtd"):
        await CommandsNamespace(transport).execute("gettime")
    assert observed is not None
    assert json.loads(observed.content) == {"command": "gettime"}
    command_records = [record for record in caplog.records if record.msg == "command.executed"]
    assert len(command_records) == 1
    assert "gettime" not in command_records[0].getMessage()
    await client.aclose()


@pytest.mark.asyncio
async def test_catalog_resources_use_observed_endpoints() -> None:
    paths: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        fixture = "items.json" if request.url.path == "/api/item" else "entity-classes.json"
        return httpx.Response(200, json=json.loads((FIXTURES / fixture).read_text()))

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    transport = HTTPTransport(
        base_url="http://configured.example",
        token_name=SecretStr("token"),
        secret=SecretStr("secret"),
        client=client,
    )
    items = await ItemsNamespace(transport, CommandsNamespace(transport)).all()
    classes = await EntitiesNamespace(transport).classes()

    assert paths == ["/api/item", "/api/entityclass"]
    assert items.get("terrStone") is not None
    assert classes.items[1].id < 0
    await client.aclose()


@pytest.mark.asyncio
async def test_item_search_posts_exact_command_and_parses_result(
    caplog: pytest.LogCaptureFixture,
) -> None:
    observed: httpx.Request | None = None

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal observed
        observed = request
        return httpx.Response(
            200,
            json=json.loads((FIXTURES / "command-listitems-two.json").read_text()),
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    transport = HTTPTransport(
        base_url="http://configured.example",
        token_name=SecretStr("token"),
        secret=SecretStr("secret"),
        client=client,
    )
    namespace = ItemsNamespace(transport, CommandsNamespace(transport))
    with caplog.at_level(logging.INFO, logger="sevendtd"):
        result = await namespace.search("resourceWood")

    assert observed is not None
    assert json.loads(observed.content) == {"command": "li resourceWood"}
    assert result.query == "resourceWood"
    assert result.names == ("resourceWoodBundle", "resourceWood")
    assert result.total == 2
    assert result.observed_at.tzinfo is not None
    assert result.raw_result.endswith("Listed 2 matching items.\n")
    command_record = next(record for record in caplog.records if record.msg == "command.executed")
    assert command_record.operation == "search_items"  # type: ignore[attr-defined]
    assert command_record.risk == "read_only"  # type: ignore[attr-defined]
    assert "resourceWood" not in command_record.getMessage()
    await client.aclose()


@pytest.mark.asyncio
async def test_typed_messages_use_exact_commands_and_redacted_logs(
    caplog: pytest.LogCaptureFixture,
) -> None:
    bodies: list[dict[str, str]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        bodies.append(body)
        command, _, parameters = body["command"].partition(" ")
        return httpx.Response(
            200,
            json={
                "data": {"command": command, "parameters": parameters, "result": "ok"},
                "meta": {"serverTime": "2026-08-22T18:55:59.7080290+00:00"},
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    transport = HTTPTransport(
        base_url="http://configured.example",
        token_name=SecretStr("token"),
        secret=SecretStr("secret"),
        client=client,
    )
    admin = AdminNamespace(CommandsNamespace(transport))
    with caplog.at_level(logging.INFO, logger="sevendtd"):
        await admin.say("private broadcast text")
        await admin.message(171, "private direct text")
        await admin.kick(171, "private kick reason")
        await admin.ban(171, 3, BanDurationUnit.MINUTE, "private ban reason")
        await admin.ban_list()
        await admin.unban("EOS_private_identity")

    assert bodies == [
        {"command": 'say "private broadcast text"'},
        {"command": 'pm 171 "private direct text"'},
        {"command": 'kick 171 "private kick reason"'},
        {"command": 'ban add 171 3 minute "private ban reason"'},
        {"command": "ban list"},
        {"command": "ban remove EOS_private_identity"},
    ]
    records = [record for record in caplog.records if record.msg == "command.executed"]
    assert [(record.operation, record.risk) for record in records] == [  # type: ignore[attr-defined]
        ("say", "mutating"),
        ("message", "mutating"),
        ("kick", "mutating"),
        ("ban", "destructive"),
        ("ban_list", "read_only"),
        ("unban", "mutating"),
    ]
    logs = " ".join(record.getMessage() for record in caplog.records)
    assert "private broadcast text" not in logs
    assert "private direct text" not in logs
    assert "private kick reason" not in logs
    assert "private ban reason" not in logs
    assert "EOS_private_identity" not in logs
    await client.aclose()
