import json
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

import sevendtd.cli.app as cli_module
from sevendtd.models.map import MapTile, RawTileCoordinate

runner = CliRunner()


def locate_result() -> dict[str, object]:
    return {
        "position": {"x": 563.0625, "z": -506.78125},
        "tile": {"zoom": 2, "coord_a": 1, "coord_b": -1},
        "span": 512.0,
        "bounds": {
            "min_x": 512.0,
            "max_x": 1024.0,
            "min_z": -512.0,
            "max_z": 0.0,
            "min_x_inclusive": True,
            "max_x_inclusive": False,
            "min_z_inclusive": False,
            "max_z_inclusive": True,
        },
        "evidence_identifier": "7dtd-v3.1.0-b14-dashboard-22c85370",
    }


def test_map_locate_json(monkeypatch: Any) -> None:
    monkeypatch.setattr(cli_module, "run", lambda state, operation: locate_result())

    result = runner.invoke(
        cli_module.app,
        ["map", "locate", "--x", "563.0625", "--z", "-506.78125", "--zoom", "2", "--json"],
    )

    assert result.exit_code == 0
    assert '"coord_a":1' in result.stdout
    assert '"coord_b":-1' in result.stdout
    assert '"min_z_inclusive":false' in result.stdout
    assert '"max_z_inclusive":true' in result.stdout


def test_map_locate_human(monkeypatch: Any) -> None:
    monkeypatch.setattr(cli_module, "run", lambda state, operation: locate_result())

    result = runner.invoke(
        cli_module.app,
        ["map", "locate", "--x", "563.0625", "--z", "-506.78125", "--zoom", "2"],
    )

    assert result.exit_code == 0
    assert "coord_a" in result.stdout
    assert "512.0" in result.stdout


def test_map_locate_rejects_non_native_zoom() -> None:
    result = runner.invoke(
        cli_module.app,
        ["map", "locate", "--x", "0", "--z", "0", "--zoom", "5"],
    )

    assert result.exit_code == 2


def tile() -> MapTile:
    content = b"\x89PNG\r\n\x1a\ncontent"
    return MapTile(
        coordinate=RawTileCoordinate(zoom=1, coord_a=2, coord_b=3),
        content=content,
        media_type="image/png",
        content_length=len(content),
    )


def test_map_tile_refuses_overwrite_without_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "tile.png"
    output.write_bytes(b"existing")
    calls: list[object] = []
    monkeypatch.setattr(cli_module, "run", lambda state, operation: calls.append(operation))
    result = runner.invoke(
        cli_module.app,
        [
            "map",
            "tile",
            "--zoom",
            "1",
            "--coord-a",
            "2",
            "--coord-b",
            "3",
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 2
    assert output.read_bytes() == b"existing"
    assert calls == []


def test_map_tile_atomically_replaces_with_force(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "tile.png"
    output.write_bytes(b"existing")
    monkeypatch.setattr(cli_module, "run", lambda state, operation: tile())
    result = runner.invoke(
        cli_module.app,
        [
            "map",
            "tile",
            "--zoom",
            "1",
            "--coord-a",
            "2",
            "--coord-b",
            "3",
            "--output",
            str(output),
            "--force",
            "--json",
        ],
    )
    assert result.exit_code == 0
    assert output.read_bytes() == tile().content
    assert json.loads(result.stdout)["path"] == str(output)


def test_map_tile_replace_failure_leaves_no_partial_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "tile.png"
    monkeypatch.setattr(cli_module, "run", lambda state, operation: tile())

    def fail_replace(source: Path, destination: Path) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr(cli_module.os, "replace", fail_replace)
    result = runner.invoke(
        cli_module.app,
        [
            "map",
            "tile",
            "--zoom",
            "1",
            "--coord-a",
            "2",
            "--coord-b",
            "3",
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 1
    assert not output.exists()
    assert list(tmp_path.iterdir()) == []


def test_mosaic_default_grid_limit_and_explicit_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[object] = []

    def fake_run(state: object, operation: object) -> dict[str, object]:
        calls.append(operation)
        return {"entries": []}

    monkeypatch.setattr(cli_module, "run", fake_run)
    base = [
        "map",
        "mosaic",
        "--zoom",
        "1",
        "--a-start",
        "0",
        "--a-end",
        "32",
        "--b-start",
        "0",
        "--b-end",
        "32",
        "--output",
        str(tmp_path / "mosaic.png"),
        "--manifest",
        str(tmp_path / "manifest.json"),
    ]
    refused = runner.invoke(cli_module.app, base)
    exact_limit = runner.invoke(
        cli_module.app,
        [value if value != "32" else "31" for value in base],
    )
    allowed = runner.invoke(cli_module.app, [*base, "--allow-large-grid"])
    assert refused.exit_code == 2
    assert exact_limit.exit_code == 0
    assert allowed.exit_code == 0
    assert len(calls) == 2
