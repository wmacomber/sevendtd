import asyncio
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager

import pytest

from sevendtd.exceptions import (
    SevenDTDAPIError,
    SevenDTDAuthenticationError,
    SevenDTDConnectionError,
    SevenDTDSSEError,
    SevenDTDTimeoutError,
)
from sevendtd.models.logs import (
    LogLineEvent,
    MalformedLogEvent,
    ReconnectPolicy,
    UnknownLogEvent,
)
from sevendtd.resources.logs import LogsNamespace, decode_log_event
from sevendtd.transport.sse import parse_sse


async def lines(values: list[str]):
    for value in values:
        yield value


@pytest.mark.asyncio
async def test_sse_parser_comments_multiline_and_id() -> None:
    frames = [
        frame
        async for frame in parse_sse(
            lines([": keepalive", "event: future", "id: abc", "data: one", "data: two", ""])
        )
    ]
    assert frames[0].event == "future"
    assert frames[0].event_id == "abc"
    assert frames[0].data == "one\ntwo"
    assert isinstance(decode_log_event(frames[0]), UnknownLogEvent)


def test_known_log_event_and_malformed_event() -> None:
    from sevendtd.models.logs import SSEFrame

    good = SSEFrame(
        "logLine",
        '{"id":1,"msg":"x","type":"Log","trace":null,"isotime":"2026-01-01T00:00:00Z","uptime":"1"}',
    )
    assert isinstance(decode_log_event(good), LogLineEvent)
    assert isinstance(decode_log_event(SSEFrame("logLine", "{")), MalformedLogEvent)


LOG_DATA = (
    '{"id":99,"msg":"x","type":"Log","trace":null,"isotime":"2026-01-01T00:00:00Z","uptime":"1"}'
)


class FakeResponse:
    def __init__(self, values: list[str] | BaseException) -> None:
        self.values = values

    async def aiter_lines(self) -> AsyncIterator[str]:
        if isinstance(self.values, BaseException):
            raise self.values
        for value in self.values:
            await asyncio.sleep(0)
            yield value


class FakeTransport:
    def __init__(self, outcomes: list[list[str] | BaseException]) -> None:
        self.outcomes = outcomes
        self.headers: list[Mapping[str, str] | None] = []

    @asynccontextmanager
    async def stream(
        self, endpoint: str, *, resource: str, headers: Mapping[str, str] | None = None
    ) -> AsyncIterator[FakeResponse]:
        assert endpoint == "/sse/?events=log"
        assert resource == "logs.stream"
        self.headers.append(headers)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        yield FakeResponse(outcome)


@pytest.mark.asyncio
async def test_clean_disconnect_without_reconnect_is_an_error() -> None:
    transport = FakeTransport([[]])
    stream = LogsNamespace(transport).stream()  # type: ignore[arg-type]
    with pytest.raises(SevenDTDSSEError, match="disconnected"):
        await anext(stream)


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [408, 429, 500, 503])
async def test_transient_http_status_retries(status: int) -> None:
    transport = FakeTransport(
        [SevenDTDAPIError("/sse/", status), ["event: logLine", f"data: {LOG_DATA}", ""]]
    )
    delays: list[float] = []

    async def sleep(delay: float) -> None:
        delays.append(delay)

    stream = LogsNamespace(transport, sleep=sleep, jitter=lambda: 0).stream(  # type: ignore[arg-type]
        reconnect=ReconnectPolicy(max_attempts=1, initial_delay=0.25)
    )
    assert isinstance(await anext(stream), LogLineEvent)
    assert delays == [0.25]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failure",
    [SevenDTDConnectionError("offline"), SevenDTDTimeoutError("stream timed out")],
)
async def test_transient_network_failure_retries(failure: Exception) -> None:
    transport = FakeTransport([failure, ["event: logLine", f"data: {LOG_DATA}", ""]])

    async def sleep(_delay: float) -> None:
        return None

    stream = LogsNamespace(transport, sleep=sleep, jitter=lambda: 0).stream(  # type: ignore[arg-type]
        reconnect=ReconnectPolicy(max_attempts=1, initial_delay=0)
    )
    assert isinstance(await anext(stream), LogLineEvent)
    assert len(transport.headers) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [400, 404, 422])
async def test_non_transient_client_status_stops_immediately(status: int) -> None:
    transport = FakeTransport([SevenDTDAPIError("/sse/", status)])
    stream = LogsNamespace(transport).stream(  # type: ignore[arg-type]
        reconnect=ReconnectPolicy(max_attempts=3)
    )
    with pytest.raises(SevenDTDAPIError) as captured:
        await anext(stream)
    assert captured.value.status_code == status
    assert len(transport.headers) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [401, 403])
async def test_authentication_stops_immediately(status: int) -> None:
    transport = FakeTransport([SevenDTDAuthenticationError("/sse/", status)])
    stream = LogsNamespace(transport).stream(  # type: ignore[arg-type]
        reconnect=ReconnectPolicy(max_attempts=3)
    )
    with pytest.raises(SevenDTDAuthenticationError):
        await anext(stream)
    assert len(transport.headers) == 1


def test_backoff_is_capped_with_deterministic_jitter() -> None:
    policy = ReconnectPolicy(initial_delay=1, maximum_delay=3, factor=2, jitter_ratio=0.25)
    assert policy.delay_for(1, 1) == 1.25
    assert policy.delay_for(2, -1) == 1.5
    assert policy.delay_for(3, 1) == 3.75
    assert policy.delay_for(20, -1) == 2.25


@pytest.mark.asyncio
async def test_cancellation_during_reading_propagates() -> None:
    transport = FakeTransport([asyncio.CancelledError()])
    stream = LogsNamespace(transport).stream(  # type: ignore[arg-type]
        reconnect=ReconnectPolicy(max_attempts=3)
    )
    with pytest.raises(asyncio.CancelledError):
        await anext(stream)


@pytest.mark.asyncio
async def test_cancellation_during_backoff_propagates() -> None:
    transport = FakeTransport([SevenDTDConnectionError("offline")])

    async def cancel(_delay: float) -> None:
        raise asyncio.CancelledError

    stream = LogsNamespace(transport, sleep=cancel).stream(  # type: ignore[arg-type]
        reconnect=ReconnectPolicy(max_attempts=3)
    )
    with pytest.raises(asyncio.CancelledError):
        await anext(stream)


@pytest.mark.asyncio
async def test_resume_cursor_requires_sse_id_not_json_payload_id() -> None:
    transport = FakeTransport(
        [
            ["event: logLine", f"data: {LOG_DATA}", ""],
            ["event: logLine", "id: cursor-1", f"data: {LOG_DATA}", ""],
            ["event: logLine", f"data: {LOG_DATA}", ""],
        ]
    )

    async def sleep(_delay: float) -> None:
        return None

    stream = LogsNamespace(transport, sleep=sleep, jitter=lambda: 0).stream(  # type: ignore[arg-type]
        reconnect=ReconnectPolicy(max_attempts=2, initial_delay=0)
    )
    first = await anext(stream)
    second = await anext(stream)
    third = await anext(stream)
    assert isinstance(first, LogLineEvent)
    assert first.event_id is None
    assert second.event_id == "cursor-1"
    assert third.event_id is None
    assert transport.headers == [None, None, {"Last-Event-ID": "cursor-1"}]


@pytest.mark.asyncio
async def test_reconnect_attempt_exhaustion_counts_retries() -> None:
    transport = FakeTransport([SevenDTDConnectionError("offline") for _ in range(3)])
    delays: list[float] = []

    async def sleep(delay: float) -> None:
        delays.append(delay)

    stream = LogsNamespace(transport, sleep=sleep, jitter=lambda: 0).stream(  # type: ignore[arg-type]
        reconnect=ReconnectPolicy(max_attempts=2, initial_delay=1, factor=2)
    )
    with pytest.raises(SevenDTDSSEError, match="attempts exhausted"):
        await anext(stream)
    assert len(transport.headers) == 3
    assert delays == [1, 2]
