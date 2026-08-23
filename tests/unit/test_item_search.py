import json
from pathlib import Path

import pytest

from sevendtd.exceptions import SevenDTDCommandError
from sevendtd.models.commands import CommandResult
from sevendtd.models.common import ResponseEnvelope
from sevendtd.resources.items import parse_item_search_result

FIXTURES = Path(__file__).parents[1] / "fixtures"


def fixture_result(name: str) -> CommandResult:
    envelope = ResponseEnvelope.model_validate(json.loads((FIXTURES / name).read_text()))
    return CommandResult.model_validate(
        {**envelope.data, "observed_at": envelope.meta.server_time}  # type: ignore[arg-type]
    )


def test_parse_observed_item_search_results() -> None:
    matches = parse_item_search_result("resourceWood", fixture_result("command-listitems-two.json"))
    empty = parse_item_search_result("resourceTool", fixture_result("command-listitems-zero.json"))

    assert matches.names == ("resourceWoodBundle", "resourceWood")
    assert matches.total == 2
    assert empty.names == ()
    assert empty.total == 0


def test_parser_accepts_crlf_and_trailing_blank_lines() -> None:
    result = fixture_result("command-listitems-two.json").model_copy(
        update={"result": "    resourceWood\r\nListed 1 matching items.\r\n\r\n"}
    )
    parsed = parse_item_search_result("resourceWood", result)
    assert parsed.names == ("resourceWood",)


@pytest.mark.parametrize(
    "raw",
    [
        "    resourceWood\n",
        "    resourceWood\nListed 2 matching items.\n",
        "resourceWood\nListed 1 matching items.\n",
        "    resource Wood\nListed 1 matching items.\n",
        "    resource;shutdown\nListed 1 matching items.\n",
        "Listed nope matching items.\n",
    ],
)
def test_parser_rejects_malformed_output(raw: str) -> None:
    result = fixture_result("command-listitems-zero.json").model_copy(update={"result": raw})
    with pytest.raises(SevenDTDCommandError):
        parse_item_search_result("resourceWood", result)
