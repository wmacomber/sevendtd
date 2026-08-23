from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from sevendtd.models.common import ResponseMeta
from sevendtd.models.entities import AnimalRecord
from sevendtd.models.map import MapConfigData, RawTileCoordinate
from sevendtd.models.server import ServerInfo, ServerProperty


def test_server_info_preserves_unknown_and_duplicates() -> None:
    info = ServerInfo(
        properties=(
            ServerProperty(name="Future", type="future", value={"x": 1}),
            ServerProperty(name="Future", type="string", value="latest"),
        ),
        observed_at=datetime.now(UTC),
    )
    assert info.get("Future") == "latest"
    assert len(info.get_all("Future")) == 2


def test_known_property_type_mismatch_fails() -> None:
    with pytest.raises(ValidationError):
        ServerProperty(name="MaxPlayers", type="int", value="8")


def test_animal_is_opaque() -> None:
    record = AnimalRecord({"future": {"shape": True}})
    assert record.root["future"] == {"shape": True}


def test_server_time_must_be_timezone_aware() -> None:
    with pytest.raises(ValidationError):
        ResponseMeta(serverTime="2026-08-21T21:12:06")


def test_protocol_models_preserve_unknown_fields_and_accept_alias_or_field_name() -> None:
    aliased = MapConfigData.model_validate(
        {
            "enabled": True,
            "mapBlockSize": 128,
            "maxZoom": 4,
            "mapSize": {"x": 1, "y": 2, "z": 3},
            "futureField": {"shape": True},
        }
    )
    named = MapConfigData.model_validate(
        {
            "enabled": True,
            "map_block_size": 128,
            "max_zoom": 4,
            "map_size": {"x": 1, "y": 2, "z": 3},
        }
    )
    assert aliased.map_block_size == named.map_block_size == 128
    assert aliased.model_extra == {"futureField": {"shape": True}}


def test_tile_coordinate_rejects_negative_zoom() -> None:
    with pytest.raises(ValidationError):
        RawTileCoordinate(zoom=-1, coord_a=0, coord_b=0)
