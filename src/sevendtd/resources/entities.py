"""Entity resources."""

from sevendtd.models.catalogs import EntityClass, EntityClassCatalog
from sevendtd.models.entities import AnimalCollection, AnimalRecord, Hostile, HostileCollection
from sevendtd.transport.http import HTTPTransport


class EntitiesNamespace:
    def __init__(self, transport: HTTPTransport) -> None:
        self._transport = transport

    async def hostiles(self) -> HostileCollection:
        data, meta = await self._transport.request_json(
            "GET", "/api/hostile", list[Hostile], resource="entities.hostiles"
        )
        return HostileCollection(items=tuple(data), observed_at=meta.server_time)

    async def animals(self) -> AnimalCollection:
        data, meta = await self._transport.request_json(
            "GET", "/api/animal", list[AnimalRecord], resource="entities.animals"
        )
        return AnimalCollection(items=tuple(data), observed_at=meta.server_time)

    async def classes(self) -> EntityClassCatalog:
        data, meta = await self._transport.request_json(
            "GET", "/api/entityclass", list[EntityClass], resource="entities.classes"
        )
        return EntityClassCatalog(items=tuple(data), observed_at=meta.server_time)

    async def search_classes(self, query: str) -> EntityClassCatalog:
        return (await self.classes()).search(query)
