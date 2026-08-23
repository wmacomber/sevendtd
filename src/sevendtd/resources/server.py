"""Server resources."""

from sevendtd.models.server import ServerInfo, ServerProperty, ServerStats, ServerStatsData
from sevendtd.transport.http import HTTPTransport


class ServerNamespace:
    def __init__(self, transport: HTTPTransport) -> None:
        self._transport = transport

    async def info(self) -> ServerInfo:
        data, meta = await self._transport.request_json(
            "GET", "/api/serverinfo", list[ServerProperty], resource="server.info"
        )
        return ServerInfo(properties=tuple(data), observed_at=meta.server_time)

    async def stats(self) -> ServerStats:
        data, meta = await self._transport.request_json(
            "GET", "/api/serverstats", ServerStatsData, resource="server.stats"
        )
        return ServerStats(**data.model_dump(), observed_at=meta.server_time)
