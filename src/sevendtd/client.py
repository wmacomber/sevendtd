"""Public async client and namespace composition."""

import asyncio
from datetime import UTC, datetime
from typing import Any, Self

import httpx

from sevendtd.admin.namespace import AdminNamespace
from sevendtd.config import SevenDTDSettings
from sevendtd.exceptions import (
    SevenDTDAuthenticationError,
    SevenDTDError,
    SevenDTDSnapshotError,
    SnapshotErrorDetail,
)
from sevendtd.models.snapshot import ServerSnapshot, SnapshotFailure
from sevendtd.resources.commands import CommandsNamespace
from sevendtd.resources.entities import EntitiesNamespace
from sevendtd.resources.items import ItemsNamespace
from sevendtd.resources.logs import LogsNamespace
from sevendtd.resources.map import MapNamespace
from sevendtd.resources.players import PlayersNamespace
from sevendtd.resources.server import ServerNamespace
from sevendtd.transport.http import HTTPTransport


class AsyncSevenDTDClient:
    def __init__(self, transport: HTTPTransport) -> None:
        self._transport = transport
        self.server = ServerNamespace(transport)
        self.players = PlayersNamespace(transport)
        self.entities = EntitiesNamespace(transport)
        self.commands = CommandsNamespace(transport)
        self.items = ItemsNamespace(transport, self.commands)
        self.logs = LogsNamespace(transport)
        self.map = MapNamespace(transport)
        self.admin = AdminNamespace(self.commands)

    @classmethod
    def from_settings(
        cls,
        settings: SevenDTDSettings,
        *,
        http_client: httpx.AsyncClient | None = None,
        owns_http_client: bool | None = None,
    ) -> Self:
        return cls(
            HTTPTransport(
                base_url=str(settings.base_url),
                token_name=settings.token_name,
                secret=settings.secret,
                timeout=settings.timeout,
                client=http_client,
                owns_client=owns_http_client,
            )
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_args: object) -> None:
        await self.close()

    async def close(self) -> None:
        await self._transport.close()

    async def snapshot(self, *, strict: bool = False) -> ServerSnapshot:
        started = datetime.now(UTC)
        names = (
            "server_info",
            "server_stats",
            "online_players",
            "hostiles",
            "animals",
            "map_config",
        )
        calls = (
            self.server.info(),
            self.server.stats(),
            self.players.online(),
            self.entities.hostiles(),
            self.entities.animals(),
            self.map.config(),
        )

        async def capture(call: Any) -> Any:
            try:
                return await call
            except SevenDTDAuthenticationError:
                raise
            except Exception as exc:
                return exc

        tasks = [asyncio.create_task(capture(call)) for call in calls]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
        authentication_error = next(
            (
                task.exception()
                for task in done
                if not task.cancelled()
                and isinstance(task.exception(), SevenDTDAuthenticationError)
            ),
            None,
        )
        if authentication_error is not None:
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            raise authentication_error
        results = await asyncio.gather(*tasks)

        values: dict[str, Any] = {}
        failures: list[SnapshotFailure] = []
        for name, result in zip(names, results, strict=True):
            if isinstance(result, BaseException):
                message = str(result) if isinstance(result, SevenDTDError) else f"{name} failed"
                failures.append(
                    SnapshotFailure(
                        component=name,
                        error_type=type(result).__name__,
                        message=message,
                    )
                )
            else:
                values[name] = result
        finished = datetime.now(UTC)
        if strict and failures:
            raise SevenDTDSnapshotError(
                [
                    SnapshotErrorDetail(item.component, item.error_type, item.message)
                    for item in failures
                ]
            )
        return ServerSnapshot(
            **values,
            capture_started_at=started,
            capture_finished_at=finished,
            failures=tuple(failures),
        )
