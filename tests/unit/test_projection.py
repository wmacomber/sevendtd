import json
from pathlib import Path

import httpx
import pytest
from pydantic import SecretStr

from sevendtd.exceptions import SevenDTDMapTileError
from sevendtd.models.players import WorldHorizontalPosition
from sevendtd.projection import MapProjection, MapProjectionSpec, TileCoordinate
from sevendtd.resources.map import MapNamespace
from sevendtd.transport.http import HTTPTransport

FIXTURE = Path(__file__).parents[1] / "fixtures/map/projection-observations.json"


def projection() -> MapProjection:
    return MapProjection(
        MapProjectionSpec(
            tile_size=128,
            minimum_zoom=0,
            maximum_zoom=4,
            map_size_x=6144,
            map_size_y=255,
            map_size_z=6144,
        )
    )


def test_recorded_observations_match_projection_exactly() -> None:
    evidence = json.loads(FIXTURE.read_text())
    observed = evidence["observations"]
    assert sum(row["purpose"] == "independent holdout" for row in observed) == 6
    for row in observed:
        tile = projection().world_to_tile(
            WorldHorizontalPosition(x=row["observed_x"], z=row["observed_z"]),
            row["zoom"],
        )
        assert (tile.coord_a, tile.coord_b) == (
            row["observed_coord_a"],
            row["observed_coord_b"],
        ), row["observation_id"]


@pytest.mark.parametrize(
    ("zoom", "span"),
    [(0, 2048.0), (1, 1024.0), (2, 512.0), (3, 256.0), (4, 128.0)],
)
def test_span_for_every_native_zoom(zoom: int, span: float) -> None:
    assert projection().span_for_zoom(zoom) == span


@pytest.mark.parametrize("zoom", [-1, 5])
def test_invalid_zoom_is_rejected(zoom: int) -> None:
    with pytest.raises(ValueError, match="zoom must be between"):
        projection().span_for_zoom(zoom)


@pytest.mark.parametrize(
    ("x", "z", "expected"),
    [
        (-0.001, 64.0, (-1, 0)),
        (0.0, 64.0, (0, 0)),
        (0.001, 64.0, (0, 0)),
        (64.0, -0.001, (0, -1)),
        (64.0, 0.0, (0, -1)),
        (64.0, 0.001, (0, 0)),
        (127.999, 64.0, (0, 0)),
        (128.0, 64.0, (1, 0)),
    ],
)
def test_zero_and_boundary_rules(x: float, z: float, expected: tuple[int, int]) -> None:
    tile = projection().world_to_tile(WorldHorizontalPosition(x=x, z=z), 4)
    assert (tile.coord_a, tile.coord_b) == expected
    assert projection().contains(tile, WorldHorizontalPosition(x=x, z=z))


def test_tile_bounds_and_adjacency_use_documented_edges() -> None:
    current = projection().tile_to_world_bounds(TileCoordinate(4, 0, 0))
    right = projection().tile_to_world_bounds(TileCoordinate(4, 1, 0))
    above = projection().tile_to_world_bounds(TileCoordinate(4, 0, 1))

    assert current.max_x == right.min_x
    assert current.max_z == above.min_z
    assert (current.min_x_inclusive, current.max_x_inclusive) == (True, False)
    assert (current.min_z_inclusive, current.max_z_inclusive) == (False, True)


def test_world_edges_map_to_containing_tile() -> None:
    for position in (
        WorldHorizontalPosition(x=-3072, z=-3072),
        WorldHorizontalPosition(x=3072, z=3072),
    ):
        tile = projection().world_to_tile(position, 4)
        assert projection().contains(tile, position)


@pytest.mark.asyncio
async def test_namespace_returns_projection_for_verified_config() -> None:
    fixture = Path(__file__).parents[1] / "fixtures/map-config.json"

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/map/config"
        return httpx.Response(200, json=json.loads(fixture.read_text()))

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    transport = HTTPTransport(
        base_url="http://configured.example",
        token_name=SecretStr("token"),
        secret=SecretStr("secret"),
        client=client,
    )
    observed = await MapNamespace(transport).projection()

    assert observed.spec.tile_size == 128
    assert observed.spec.maximum_zoom == 4
    assert observed.spec.map_size_x == 6144
    await client.aclose()


@pytest.mark.asyncio
async def test_namespace_rejects_unverified_config() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(
            200,
            json={
                "data": {
                    "enabled": True,
                    "mapBlockSize": 256,
                    "maxZoom": 4,
                    "mapSize": {"x": 6144, "y": 255, "z": 6144},
                },
                "meta": {"serverTime": "2026-08-23T04:06:28.277911Z"},
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    transport = HTTPTransport(
        base_url="http://configured.example",
        token_name=SecretStr("token"),
        secret=SecretStr("secret"),
        client=client,
    )
    with pytest.raises(SevenDTDMapTileError, match="mapBlockSize=256"):
        await MapNamespace(transport).projection()
    await client.aclose()
