"""Public SevenDTD library API."""

from sevendtd.admin.metadata import (
    AdminOperationMetadata,
    BanDurationUnit,
    CommandRisk,
    PreparedCommand,
)
from sevendtd.client import AsyncSevenDTDClient
from sevendtd.config import SevenDTDSettings
from sevendtd.exceptions import (
    SevenDTDAPIError,
    SevenDTDAuthenticationError,
    SevenDTDCommandError,
    SevenDTDConfigurationError,
    SevenDTDConnectionError,
    SevenDTDError,
    SevenDTDInvalidResponseError,
    SevenDTDMapTileError,
    SevenDTDSnapshotError,
    SevenDTDSSEError,
    SevenDTDTimeoutError,
    SevenDTDTransportError,
)
from sevendtd.models.catalogs import (
    EntityClass,
    EntityClassCatalog,
    ItemCatalog,
    ItemDefinition,
    ItemSearchResult,
)
from sevendtd.models.entities import AnimalCollection, AnimalRecord, Hostile, HostileCollection
from sevendtd.models.logs import (
    LogLineEvent,
    MalformedLogEvent,
    ReconnectPolicy,
    UnknownLogEvent,
)
from sevendtd.models.map import MapConfig, MapTile, RawTileCoordinate
from sevendtd.models.players import OnlinePlayers, Player, WorldHorizontalPosition, WorldPosition
from sevendtd.models.server import ServerInfo, ServerStats
from sevendtd.models.snapshot import ServerSnapshot, SnapshotFailure
from sevendtd.projection import MapProjection, MapProjectionSpec, TileCoordinate, WorldBounds

__all__ = [
    "AdminOperationMetadata",
    "AnimalCollection",
    "AnimalRecord",
    "AsyncSevenDTDClient",
    "BanDurationUnit",
    "CommandRisk",
    "EntityClass",
    "EntityClassCatalog",
    "Hostile",
    "HostileCollection",
    "ItemCatalog",
    "ItemDefinition",
    "ItemSearchResult",
    "LogLineEvent",
    "MalformedLogEvent",
    "MapConfig",
    "MapProjection",
    "MapProjectionSpec",
    "MapTile",
    "OnlinePlayers",
    "Player",
    "PreparedCommand",
    "RawTileCoordinate",
    "ReconnectPolicy",
    "ServerInfo",
    "ServerSnapshot",
    "ServerStats",
    "SevenDTDAPIError",
    "SevenDTDAuthenticationError",
    "SevenDTDCommandError",
    "SevenDTDConfigurationError",
    "SevenDTDConnectionError",
    "SevenDTDError",
    "SevenDTDInvalidResponseError",
    "SevenDTDMapTileError",
    "SevenDTDSSEError",
    "SevenDTDSettings",
    "SevenDTDSnapshotError",
    "SevenDTDTimeoutError",
    "SevenDTDTransportError",
    "SnapshotFailure",
    "TileCoordinate",
    "UnknownLogEvent",
    "WorldBounds",
    "WorldHorizontalPosition",
    "WorldPosition",
]
