"""Player resources."""

from sevendtd.models.players import OnlinePlayers, PlayersData
from sevendtd.transport.http import HTTPTransport


class PlayersNamespace:
    def __init__(self, transport: HTTPTransport) -> None:
        self._transport = transport

    async def online(self) -> OnlinePlayers:
        data, meta = await self._transport.request_json(
            "GET", "/api/player", PlayersData, resource="players.online"
        )
        return OnlinePlayers(players=data.players, observed_at=meta.server_time)
