import json
from pathlib import Path

import pytest
from pydantic import TypeAdapter

from sevendtd.models.catalogs import EntityClass, ItemDefinition
from sevendtd.models.commands import CommandData
from sevendtd.models.common import ResponseEnvelope
from sevendtd.models.entities import AnimalRecord, Hostile
from sevendtd.models.map import MapConfigData
from sevendtd.models.players import PlayersData
from sevendtd.models.server import ServerProperty, ServerStatsData

FIXTURES = Path(__file__).parents[1] / "fixtures"


@pytest.mark.parametrize(
    ("name", "data_type"),
    [
        ("serverinfo.json", list[ServerProperty]),
        ("serverstats.json", ServerStatsData),
        ("map-config.json", MapConfigData),
        ("players.json", PlayersData),
        ("hostiles.json", list[Hostile]),
        ("animals-empty.json", list[AnimalRecord]),
        ("command-help.json", CommandData),
        ("command-help-say.json", CommandData),
        ("command-help-sayplayer.json", CommandData),
        ("command-kick.json", CommandData),
        ("command-ban-add.json", CommandData),
        ("command-ban-list.json", CommandData),
        ("command-ban-remove.json", CommandData),
        ("command-ban-list-empty.json", CommandData),
        ("command-listitems-two.json", CommandData),
        ("command-listitems-zero.json", CommandData),
        ("items.json", list[ItemDefinition]),
        ("entity-classes.json", list[EntityClass]),
    ],
)
def test_captured_fixture_parses(name: str, data_type: object) -> None:
    raw = json.loads((FIXTURES / name).read_text())
    envelope = ResponseEnvelope.model_validate(raw)
    assert envelope.meta.server_time.tzinfo is not None
    TypeAdapter(data_type).validate_python(envelope.data)


def test_fixtures_do_not_contain_authentication_headers() -> None:
    for path in FIXTURES.rglob("*"):
        if path.is_file():
            contents = path.read_text(errors="ignore")
            assert "X-SDTD-API-TOKENNAME" not in contents
            assert "X-SDTD-API-SECRET" not in contents
