"""Pure, evidence-backed world-to-map-tile projection."""

import math
from dataclasses import dataclass

from sevendtd.models.players import WorldHorizontalPosition

VERIFIED_EVIDENCE_ID = "7dtd-v3.1.0-b14-dashboard-22c85370"


@dataclass(frozen=True, slots=True)
class TileCoordinate:
    zoom: int
    coord_a: int
    coord_b: int


@dataclass(frozen=True, slots=True)
class WorldBounds:
    """Tile bounds: X is lower-inclusive; Z is upper-inclusive."""

    min_x: float
    max_x: float
    min_z: float
    max_z: float
    min_x_inclusive: bool = True
    max_x_inclusive: bool = False
    min_z_inclusive: bool = False
    max_z_inclusive: bool = True


@dataclass(frozen=True, slots=True)
class TilePixel:
    """Reserved value type. Pixel projection remains unverified."""

    column: int
    row: int


@dataclass(frozen=True, slots=True)
class MapProjectionSpec:
    tile_size: int
    minimum_zoom: int
    maximum_zoom: int
    map_size_x: int
    map_size_y: int
    map_size_z: int
    evidence_identifier: str = VERIFIED_EVIDENCE_ID

    def __post_init__(self) -> None:
        if self.tile_size <= 0:
            raise ValueError("tile_size must be positive")
        if self.minimum_zoom < 0 or self.maximum_zoom < self.minimum_zoom:
            raise ValueError("invalid projection zoom range")
        if min(self.map_size_x, self.map_size_y, self.map_size_z) <= 0:
            raise ValueError("map dimensions must be positive")
        if not self.evidence_identifier:
            raise ValueError("evidence_identifier must not be empty")


class MapProjection:
    """Verified native tile projection for the supported dashboard transform."""

    def __init__(self, spec: MapProjectionSpec) -> None:
        self.spec = spec

    def span_for_zoom(self, zoom: int) -> float:
        self._validate_zoom(zoom)
        return float(self.spec.tile_size * 2 ** (self.spec.maximum_zoom - zoom))

    def world_to_tile(self, position: WorldHorizontalPosition, zoom: int) -> TileCoordinate:
        self._validate_position(position)
        span = self.span_for_zoom(zoom)
        return TileCoordinate(
            zoom=zoom,
            coord_a=math.floor(position.x / span),
            coord_b=-math.floor(-position.z / span) - 1,
        )

    def tile_to_world_bounds(self, tile: TileCoordinate) -> WorldBounds:
        span = self.span_for_zoom(tile.zoom)
        return WorldBounds(
            min_x=tile.coord_a * span,
            max_x=(tile.coord_a + 1) * span,
            min_z=tile.coord_b * span,
            max_z=(tile.coord_b + 1) * span,
        )

    def contains(self, tile: TileCoordinate, position: WorldHorizontalPosition) -> bool:
        self._validate_position(position)
        bounds = self.tile_to_world_bounds(tile)
        return (
            bounds.min_x <= position.x < bounds.max_x and bounds.min_z < position.z <= bounds.max_z
        )

    def _validate_zoom(self, zoom: int) -> None:
        if isinstance(zoom, bool):
            raise TypeError("zoom must be an integer")
        if not self.spec.minimum_zoom <= zoom <= self.spec.maximum_zoom:
            raise ValueError(
                f"zoom must be between {self.spec.minimum_zoom} and {self.spec.maximum_zoom}"
            )

    @staticmethod
    def _validate_position(position: WorldHorizontalPosition) -> None:
        if not math.isfinite(position.x) or not math.isfinite(position.z):
            raise ValueError("world position coordinates must be finite")
