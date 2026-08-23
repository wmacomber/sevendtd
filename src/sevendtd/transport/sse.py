"""Incremental Server-Sent Events framing."""

from collections.abc import AsyncIterable, AsyncIterator

from sevendtd.models.logs import SSEFrame


async def parse_sse(lines: AsyncIterable[str]) -> AsyncIterator[SSEFrame]:
    event_name = "message"
    data_lines: list[str] = []
    event_id: str | None = None
    retry: int | None = None

    async for line in lines:
        if line == "":
            if data_lines:
                yield SSEFrame(
                    event=event_name,
                    data="\n".join(data_lines),
                    event_id=event_id,
                    retry=retry,
                )
            event_name = "message"
            data_lines = []
            retry = None
            continue
        if line.startswith(":"):
            continue
        field, separator, value = line.partition(":")
        if separator and value.startswith(" "):
            value = value[1:]
        if field == "event":
            event_name = value
        elif field == "data":
            data_lines.append(value)
        elif field == "id" and "\x00" not in value:
            event_id = value
        elif field == "retry" and value.isdigit():
            retry = int(value)

    if data_lines:
        yield SSEFrame(
            event=event_name,
            data="\n".join(data_lines),
            event_id=event_id,
            retry=retry,
        )
