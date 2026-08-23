"""Read-only item and entity-class catalog models."""

from typing import Any

from pydantic import AwareDatetime, Field, PrivateAttr

from sevendtd.models.common import ProtocolModel


class ItemDefinition(ProtocolModel):
    name: str
    localized_name: str = Field(alias="localizedName")
    is_block: bool = Field(alias="isBlock")


class ItemCatalog(ProtocolModel):
    items: tuple[ItemDefinition, ...]
    observed_at: AwareDatetime
    _index: dict[str, tuple[ItemDefinition, ...]] = PrivateAttr(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        index: dict[str, list[ItemDefinition]] = {}
        for item in self.items:
            index.setdefault(item.name, []).append(item)
        self._index = {name: tuple(items) for name, items in index.items()}

    def get(self, name: str) -> ItemDefinition | None:
        matches = self._index.get(name)
        return matches[-1] if matches else None

    def get_all(self, name: str) -> tuple[ItemDefinition, ...]:
        return self._index.get(name, ())

    def search(self, query: str, *, blocks_only: bool = False) -> "ItemCatalog":
        needle = query.casefold()
        return ItemCatalog(
            items=tuple(
                item
                for item in self.items
                if (not blocks_only or item.is_block)
                and (needle in item.name.casefold() or needle in item.localized_name.casefold())
            ),
            observed_at=self.observed_at,
        )


class ItemSearchResult(ProtocolModel):
    query: str
    names: tuple[str, ...]
    total: int
    observed_at: AwareDatetime
    raw_result: str


class EntityClass(ProtocolModel):
    name: str
    id: int
    manual_spawn_type: str = Field(alias="manualSpawnType")


class EntityClassCatalog(ProtocolModel):
    items: tuple[EntityClass, ...]
    observed_at: AwareDatetime

    def search(self, query: str) -> "EntityClassCatalog":
        needle = query.casefold()
        return EntityClassCatalog(
            items=tuple(item for item in self.items if needle in item.name.casefold()),
            observed_at=self.observed_at,
        )
