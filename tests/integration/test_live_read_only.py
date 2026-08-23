import os

import pytest

from sevendtd import AsyncSevenDTDClient, SevenDTDSettings

pytestmark = [pytest.mark.integration, pytest.mark.enable_socket]


@pytest.mark.asyncio
async def test_live_observed_read_only_resources() -> None:
    async with AsyncSevenDTDClient.from_settings(SevenDTDSettings.from_environment()) as client:
        info = await client.server.info()
        stats = await client.server.stats()
        players = await client.players.online()
        hostiles = await client.entities.hostiles()
        animals = await client.entities.animals()
        items = await client.items.all()
        item_search = await client.items.search(items.items[0].name)
        entity_classes = await client.entities.classes()
        config = await client.map.config()

    assert info.observed_at.tzinfo is not None
    assert stats.observed_at.tzinfo is not None
    assert players.observed_at.tzinfo is not None
    assert hostiles.observed_at.tzinfo is not None
    assert animals.observed_at.tzinfo is not None
    assert items.observed_at.tzinfo is not None
    assert items.items[0].name in item_search.names
    assert entity_classes.observed_at.tzinfo is not None
    assert config.map_block_size > 0


@pytest.mark.asyncio
async def test_live_gettime_command() -> None:
    async with AsyncSevenDTDClient.from_settings(SevenDTDSettings.from_environment()) as client:
        result = await client.admin.get_time()
    assert result.command in {"gettime", "gt"}


@pytest.mark.asyncio
async def test_live_known_tile_when_coordinates_supplied() -> None:
    required = ("SEVENTDTD_TEST_TILE_ZOOM", "SEVENTDTD_TEST_TILE_A", "SEVENTDTD_TEST_TILE_B")
    if not all(name in os.environ for name in required):
        pytest.skip("known live tile coordinates not configured")
    async with AsyncSevenDTDClient.from_settings(SevenDTDSettings.from_environment()) as client:
        tile = await client.map.tile(
            zoom=int(os.environ[required[0]]),
            coord_a=int(os.environ[required[1]]),
            coord_b=int(os.environ[required[2]]),
        )
    assert tile.content.startswith(b"\x89PNG\r\n\x1a\n")


@pytest.mark.mutating
@pytest.mark.asyncio
async def test_live_give_one_configured_item() -> None:
    entity_id = os.getenv("SEVENTDTD_TEST_GIVE_ENTITY_ID")
    item_name = os.getenv("SEVENTDTD_TEST_GIVE_ITEM_NAME")
    if entity_id is None or item_name is None:
        pytest.skip("live give target and item not configured")
    async with AsyncSevenDTDClient.from_settings(SevenDTDSettings.from_environment()) as client:
        catalog = await client.items.all()
        assert catalog.get(item_name) is not None
        result = await client.admin.give(int(entity_id), item_name, 1)
    assert result.command == "give"
