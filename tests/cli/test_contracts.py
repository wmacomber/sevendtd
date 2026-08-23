import json
from datetime import UTC, datetime
from typing import Any

import pytest
import typer
from typer.testing import CliRunner

import sevendtd.cli.app as cli_module
from sevendtd.cli.errors import exit_code
from sevendtd.exceptions import (
    SevenDTDAPIError,
    SevenDTDAuthenticationError,
    SevenDTDConfigurationError,
    SevenDTDConnectionError,
    SevenDTDError,
    SevenDTDInvalidResponseError,
    SevenDTDTimeoutError,
)
from sevendtd.models.logs import UnknownLogEvent
from sevendtd.models.server import ServerInfo, ServerProperty
from sevendtd.models.snapshot import ServerSnapshot, SnapshotFailure

runner = CliRunner()


def partial_snapshot(*, with_success: bool = False) -> ServerSnapshot:
    now = datetime.now(UTC)
    info = None
    if with_success:
        info = ServerInfo(
            properties=(ServerProperty(name="GameName", type="string", value="Test World"),),
            observed_at=now,
        )
    return ServerSnapshot(
        server_info=info,
        capture_started_at=now,
        capture_finished_at=now,
        failures=(
            SnapshotFailure(
                component="server_stats",
                error_type="SevenDTDAPIError",
                message="upstream request failed for /api/serverstats (HTTP 500)",
            ),
        ),
    )


def test_finite_json_is_one_valid_document(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli_module, "run", lambda state, operation: partial_snapshot())
    result = runner.invoke(cli_module.app, ["status", "--json"])
    assert result.exit_code == 6
    assert json.loads(result.stdout)["failures"][0]["component"] == "server_stats"
    assert result.stdout.count("\n") == 1


def test_human_status_shows_successes_and_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        cli_module, "run", lambda state, operation: partial_snapshot(with_success=True)
    )
    result = runner.invoke(cli_module.app, ["status"])
    assert result.exit_code == 6
    assert "server_info" in result.stdout
    assert "Test World" in result.stdout
    assert "server_stats" in result.stdout
    assert "failed" in result.stdout
    assert "HTTP 500" in result.stdout


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (SevenDTDConfigurationError("bad config"), 3),
        (SevenDTDAuthenticationError("/api/serverinfo", 401), 3),
        (SevenDTDConnectionError("offline"), 4),
        (SevenDTDTimeoutError("slow"), 4),
        (SevenDTDAPIError("/api/serverinfo", 500), 5),
        (SevenDTDInvalidResponseError("bad payload"), 5),
        (SevenDTDError("other"), 5),
    ],
)
def test_documented_exception_exit_mapping(error: SevenDTDError, expected: int) -> None:
    assert exit_code(error) == expected


def test_diagnostics_use_stderr_only(monkeypatch: pytest.MonkeyPatch) -> None:
    class FailingClient:
        async def __aenter__(self) -> Any:
            raise SevenDTDConnectionError("server unavailable")

        async def __aexit__(self, *_args: object) -> None:
            return None

    monkeypatch.setattr(cli_module.CLIState, "settings", lambda self: object())
    monkeypatch.setattr(
        cli_module.AsyncSevenDTDClient,
        "from_settings",
        classmethod(lambda cls, settings: FailingClient()),
    )
    result = runner.invoke(cli_module.app, ["players", "--json"])
    assert result.exit_code == 4
    assert result.stdout == ""
    assert "server unavailable" in result.stderr


@pytest.mark.parametrize("error", [EOFError(), KeyboardInterrupt()])
def test_console_eof_and_ctrl_c_exit_130_without_execution(
    error: BaseException, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[object] = []
    monkeypatch.setattr(typer, "prompt", lambda *args, **kwargs: (_ for _ in ()).throw(error))
    monkeypatch.setattr(cli_module, "run", lambda state, operation: calls.append(operation))
    result = runner.invoke(cli_module.app, ["console"], input="y\n")
    assert result.exit_code == 130
    assert calls == []


@pytest.mark.parametrize(
    ("arguments", "expected_attempts"),
    [(["logs", "--json", "--no-reconnect"], None), (["logs", "--json", "--max-retries", "2"], 2)],
)
def test_logs_json_is_ndjson_and_reconnect_flag_is_honored(
    arguments: list[str], expected_attempts: int | None, monkeypatch: pytest.MonkeyPatch
) -> None:
    observed: list[object] = []

    class Logs:
        async def stream(self, *, reconnect: object):
            observed.append(reconnect)
            yield UnknownLogEvent(event_type="future", raw_data="x" * 500)
            yield UnknownLogEvent(event_type="future", raw_data="second")

    class FakeClient:
        logs = Logs()

        async def __aenter__(self) -> "FakeClient":
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

    monkeypatch.setattr(cli_module.CLIState, "settings", lambda self: object())
    monkeypatch.setattr(
        cli_module.AsyncSevenDTDClient,
        "from_settings",
        classmethod(lambda cls, settings: FakeClient()),
    )
    result = runner.invoke(cli_module.app, arguments)
    assert result.exit_code == 0
    documents = [json.loads(line) for line in result.stdout.splitlines()]
    assert [document["raw_data"] for document in documents] == ["x" * 500, "second"]
    policy = observed[0]
    assert (None if policy is None else policy.max_attempts) == expected_attempts


def test_logs_keyboard_interrupt_maps_to_cancellation(monkeypatch: pytest.MonkeyPatch) -> None:
    def interrupt(coroutine: Any) -> None:
        coroutine.close()
        raise KeyboardInterrupt

    monkeypatch.setattr(cli_module.asyncio, "run", interrupt)
    result = runner.invoke(cli_module.app, ["logs"])
    assert result.exit_code == 130


def test_logs_failure_closes_client_and_uses_stderr(monkeypatch: pytest.MonkeyPatch) -> None:
    closed: list[bool] = []

    class Logs:
        async def stream(self, *, reconnect: object):
            del reconnect
            if False:
                yield None
            raise SevenDTDConnectionError("log stream unavailable")

    class FakeClient:
        logs = Logs()

        async def __aenter__(self) -> "FakeClient":
            return self

        async def __aexit__(self, *_args: object) -> None:
            closed.append(True)

    monkeypatch.setattr(cli_module.CLIState, "settings", lambda self: object())
    monkeypatch.setattr(
        cli_module.AsyncSevenDTDClient,
        "from_settings",
        classmethod(lambda cls, settings: FakeClient()),
    )
    result = runner.invoke(cli_module.app, ["logs", "--json", "--no-reconnect"])
    assert result.exit_code == 4
    assert result.stdout == ""
    assert "log stream unavailable" in result.stderr
    assert closed == [True]
