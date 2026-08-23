"""Typed SSE log stream with explicit reconnect policy."""

import asyncio
import random
from collections.abc import AsyncIterator, Awaitable, Callable

from pydantic import ValidationError

from sevendtd.exceptions import (
    SevenDTDAPIError,
    SevenDTDAuthenticationError,
    SevenDTDConnectionError,
    SevenDTDSSEError,
    SevenDTDTimeoutError,
)
from sevendtd.logging import get_logger, safe_extra
from sevendtd.models.logs import (
    BaseLogEvent,
    LogLineEvent,
    LogLinePayload,
    MalformedLogEvent,
    ReconnectPolicy,
    SSEFrame,
    UnknownLogEvent,
)
from sevendtd.transport.http import HTTPTransport
from sevendtd.transport.sse import parse_sse

Sleep = Callable[[float], Awaitable[None]]
Jitter = Callable[[], float]


def decode_log_event(frame: SSEFrame) -> BaseLogEvent:
    if frame.event != "logLine":
        return UnknownLogEvent(
            event_type=frame.event,
            event_id=frame.event_id,
            raw_data=frame.data,
        )
    try:
        payload = LogLinePayload.model_validate_json(frame.data)
    except (ValueError, ValidationError) as exc:
        return MalformedLogEvent(
            event_type=frame.event,
            event_id=frame.event_id,
            raw_data=frame.data,
            error=f"{type(exc).__name__}: invalid logLine payload",
        )
    return LogLineEvent(
        event_type=frame.event,
        event_id=frame.event_id,
        raw_data=frame.data,
        payload=payload,
    )


class LogsNamespace:
    def __init__(
        self,
        transport: HTTPTransport,
        *,
        sleep: Sleep = asyncio.sleep,
        jitter: Jitter | None = None,
    ) -> None:
        self._transport = transport
        self._sleep = sleep
        self._jitter = jitter or (lambda: random.uniform(-1.0, 1.0))
        self._logger = get_logger()

    async def stream(
        self,
        *,
        reconnect: ReconnectPolicy | None = None,
    ) -> AsyncIterator[BaseLogEvent]:
        reconnect_attempt = 0
        last_event_id: str | None = None
        while True:
            headers = {"Last-Event-ID": last_event_id} if last_event_id is not None else None
            try:
                async with self._transport.stream(
                    "/sse/?events=log", resource="logs.stream", headers=headers
                ) as response:
                    self._logger.info(
                        "sse.connected",
                        extra=safe_extra({"resource": "logs.stream", "attempt": reconnect_attempt}),
                    )
                    async for frame in parse_sse(response.aiter_lines()):
                        if frame.event_id is not None:
                            last_event_id = frame.event_id
                        event = decode_log_event(frame)
                        if isinstance(event, MalformedLogEvent):
                            self._logger.warning(
                                "sse.event.malformed",
                                extra=safe_extra(
                                    {
                                        "resource": "logs.stream",
                                        "event_type": frame.event,
                                        "exception_category": "ValidationError",
                                    }
                                ),
                            )
                        yield event
            except SevenDTDAuthenticationError:
                raise
            except SevenDTDAPIError as exc:
                if exc.status_code not in {408, 429} and exc.status_code < 500:
                    raise
                failure: Exception = exc
            except (SevenDTDConnectionError, SevenDTDTimeoutError, SevenDTDSSEError) as exc:
                failure = exc
            else:
                failure = SevenDTDSSEError("SSE stream disconnected")

            self._logger.info(
                "sse.disconnected",
                extra=safe_extra(
                    {
                        "resource": "logs.stream",
                        "exception_category": type(failure).__name__,
                    }
                ),
            )
            if reconnect is None:
                raise SevenDTDSSEError("SSE stream disconnected") from failure
            if reconnect.max_attempts is not None and reconnect_attempt >= reconnect.max_attempts:
                raise SevenDTDSSEError("SSE reconnect attempts exhausted") from failure
            reconnect_attempt += 1
            delay = reconnect.delay_for(reconnect_attempt, self._jitter())
            self._logger.info(
                "sse.reconnect_scheduled",
                extra=safe_extra(
                    {
                        "resource": "logs.stream",
                        "attempt": reconnect_attempt,
                        "retry_delay": delay,
                    }
                ),
            )
            await self._sleep(delay)
