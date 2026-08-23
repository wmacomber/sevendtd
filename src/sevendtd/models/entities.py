"""Hostile and provisional animal models."""

from pydantic import AwareDatetime, RootModel

from sevendtd.models.common import JsonValue, ProtocolModel
from sevendtd.models.players import WorldPosition


class Hostile(ProtocolModel):
    id: int
    name: str
    position: WorldPosition


class HostileCollection(ProtocolModel):
    items: tuple[Hostile, ...]
    observed_at: AwareDatetime


class AnimalRecord(RootModel[dict[str, JsonValue]]):
    """Opaque record until a non-empty upstream shape is observed."""


class AnimalCollection(ProtocolModel):
    items: tuple[AnimalRecord, ...]
    observed_at: AwareDatetime
