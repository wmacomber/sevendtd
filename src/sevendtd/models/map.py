"""Raw map models. Coordinate semantics remain intentionally neutral."""

from pydantic import AwareDatetime, Field

from sevendtd.models.common import ProtocolModel


class MapSize(ProtocolModel):
    x: int
    y: int
    z: int


class MapConfigData(ProtocolModel):
    enabled: bool
    map_block_size: int = Field(alias="mapBlockSize")
    max_zoom: int = Field(alias="maxZoom")
    map_size: MapSize = Field(alias="mapSize")


class MapConfig(MapConfigData):
    observed_at: AwareDatetime


class RawTileCoordinate(ProtocolModel):
    zoom: int = Field(ge=0)
    coord_a: int
    coord_b: int


class MapTile(ProtocolModel):
    coordinate: RawTileCoordinate
    content: bytes
    media_type: str | None = None
    content_length: int
    etag: str | None = None
    last_modified: str | None = None
