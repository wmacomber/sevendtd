import asyncio
import hashlib
import io
from datetime import UTC, datetime
from pathlib import Path

import pytest
from PIL import Image

import sevendtd.cli.commands.map as map_tools
from sevendtd.cli.commands.map import classify_image, create_mosaic, inclusive_range
from sevendtd.exceptions import SevenDTDAuthenticationError, SevenDTDMapTileError
from sevendtd.models.map import MapConfig, MapSize, MapTile, RawTileCoordinate


def test_inclusive_ranges_preserve_requested_direction() -> None:
    assert inclusive_range(-2, 2) == [-2, -1, 0, 1, 2]
    assert inclusive_range(2, -2) == [2, 1, 0, -1, -2]


def test_alpha_classification() -> None:
    assert classify_image(Image.new("RGBA", (2, 2), (0, 0, 0, 0))) == "fully_transparent"
    assert classify_image(Image.new("RGBA", (2, 2), (0, 0, 0, 128))) == "partially_transparent"
    assert classify_image(Image.new("RGBA", (2, 2), (0, 0, 0, 255))) == "opaque"


def png_bytes(color: tuple[int, int, int, int], *, size: int = 8) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGBA", (size, size), color).save(buffer, format="PNG")
    return buffer.getvalue()


class FakeMap:
    def __init__(self, outcomes: dict[tuple[int, int], bytes | BaseException]) -> None:
        self.outcomes = outcomes
        self.requests: list[tuple[int, int, str | int | None]] = []
        self.active = 0
        self.maximum_active = 0
        self.delay = 0.0

    async def config(self) -> MapConfig:
        return MapConfig(
            enabled=True,
            mapBlockSize=8,
            maxZoom=4,
            mapSize=MapSize(x=100, y=100, z=100),
            observed_at=datetime.now(UTC),
        )

    async def tile(
        self,
        *,
        zoom: int,
        coord_a: int,
        coord_b: int,
        cache_token: str | int | None = None,
    ) -> MapTile:
        self.requests.append((coord_a, coord_b, cache_token))
        self.active += 1
        self.maximum_active = max(self.maximum_active, self.active)
        try:
            if self.delay:
                await asyncio.sleep(self.delay)
            outcome = self.outcomes[(coord_a, coord_b)]
            if isinstance(outcome, BaseException):
                raise outcome
            return MapTile(
                coordinate=RawTileCoordinate(zoom=zoom, coord_a=coord_a, coord_b=coord_b),
                content=outcome,
                media_type="image/png",
                content_length=len(outcome),
            )
        finally:
            self.active -= 1


class FakeClient:
    def __init__(self, map_namespace: FakeMap) -> None:
        self.map = map_namespace


def assert_directory_empty(path: Path) -> None:
    assert list(path.iterdir()) == []


@pytest.mark.asyncio
async def test_mosaic_preserves_direction_and_row_column_placement(tmp_path: Path) -> None:
    colors = {
        (2, 4): (255, 0, 0, 255),
        (1, 4): (0, 255, 0, 255),
        (2, 3): (0, 0, 255, 255),
        (1, 3): (255, 255, 0, 255),
    }
    namespace = FakeMap({coordinate: png_bytes(color) for coordinate, color in colors.items()})
    output, manifest = tmp_path / "mosaic.png", tmp_path / "manifest.json"
    document = await create_mosaic(
        FakeClient(namespace),  # type: ignore[arg-type]
        zoom=2,
        a_values=[2, 1],
        b_values=[4, 3],
        output=output,
        manifest=manifest,
        annotate=False,
        cache_token=None,
        concurrency=4,
    )
    with Image.open(output) as mosaic:
        assert mosaic.getpixel((4, 4)) == colors[(2, 4)]
        assert mosaic.getpixel((12, 4)) == colors[(1, 4)]
        assert mosaic.getpixel((4, 12)) == colors[(2, 3)]
        assert mosaic.getpixel((12, 12)) == colors[(1, 3)]
    assert document["a_values"] == [2, 1]
    assert document["b_values"] == [4, 3]
    assert [
        (entry["coord_a"], entry["coord_b"])  # type: ignore[index]
        for entry in document["entries"]  # type: ignore[union-attr]
    ] == [(2, 4), (1, 4), (2, 3), (1, 3)]


@pytest.mark.asyncio
async def test_mosaic_annotation_and_failed_placeholder(tmp_path: Path) -> None:
    namespace = FakeMap(
        {
            (0, 0): png_bytes((0, 0, 255, 255)),
            (1, 0): SevenDTDMapTileError("failed tile"),
        }
    )
    output, manifest = tmp_path / "mosaic.png", tmp_path / "manifest.json"
    document = await create_mosaic(
        FakeClient(namespace),  # type: ignore[arg-type]
        zoom=1,
        a_values=[0, 1],
        b_values=[0],
        output=output,
        manifest=manifest,
        annotate=True,
        cache_token=None,
        concurrency=2,
    )
    with Image.open(output) as mosaic:
        assert mosaic.getpixel((2, 2)) != (0, 0, 255, 255)
        assert mosaic.getpixel((12, 1))[:3] == (127, 29, 29)
    failed = document["entries"][1]  # type: ignore[index]
    assert failed["status"] == "failed"
    assert failed["classification"] == "request_failed"
    assert failed["error_type"] == "SevenDTDMapTileError"


@pytest.mark.asyncio
async def test_mosaic_classification_manifest_and_secret_exclusion(tmp_path: Path) -> None:
    payloads = {
        (0, 0): png_bytes((1, 2, 3, 0)),
        (1, 0): png_bytes((1, 2, 3, 128)),
        (2, 0): png_bytes((1, 2, 3, 255)),
        (3, 0): b"not a png private-auth-value",
    }
    namespace = FakeMap(payloads)
    output, manifest = tmp_path / "mosaic.png", tmp_path / "manifest.json"
    document = await create_mosaic(
        FakeClient(namespace),  # type: ignore[arg-type]
        zoom=3,
        a_values=[0, 1, 2, 3],
        b_values=[0],
        output=output,
        manifest=manifest,
        annotate=False,
        cache_token="private-cache-token",
        concurrency=4,
    )
    entries = document["entries"]  # type: ignore[assignment]
    assert [entry["classification"] for entry in entries] == [  # type: ignore[index]
        "fully_transparent",
        "partially_transparent",
        "opaque",
        "invalid_png",
    ]
    assert [entry["status"] for entry in entries] == ["ok", "ok", "ok", "failed"]  # type: ignore[index]
    for coord_a, entry in enumerate(entries):  # type: ignore[arg-type]
        payload = payloads[(coord_a, 0)]
        assert entry["path"] == f"/map/3/{coord_a}/0.png"
        assert entry["byte_count"] == len(payload)
        assert entry["sha256"] == hashlib.sha256(payload).hexdigest()
    assert entries[0]["width"] == entries[0]["height"] == 8  # type: ignore[index]
    assert entries[3]["width"] is None  # type: ignore[index]
    manifest_text = manifest.read_text()
    assert "private-cache-token" not in manifest_text
    assert "private-auth-value" not in manifest_text
    assert all(request[2] == "private-cache-token" for request in namespace.requests)


@pytest.mark.asyncio
async def test_mosaic_concurrency_and_request_count(tmp_path: Path) -> None:
    namespace = FakeMap({(a, b): png_bytes((a, b, 0, 255)) for a in range(3) for b in range(2)})
    namespace.delay = 0.01
    await create_mosaic(
        FakeClient(namespace),  # type: ignore[arg-type]
        zoom=1,
        a_values=[0, 1, 2],
        b_values=[0, 1],
        output=tmp_path / "mosaic.png",
        manifest=tmp_path / "manifest.json",
        annotate=False,
        cache_token=None,
        concurrency=2,
    )
    assert len(namespace.requests) == 6
    assert namespace.maximum_active == 2


@pytest.mark.asyncio
async def test_mosaic_authentication_fails_without_artifacts(tmp_path: Path) -> None:
    namespace = FakeMap({(0, 0): SevenDTDAuthenticationError("/map", 401)})
    output, manifest = tmp_path / "mosaic.png", tmp_path / "manifest.json"
    with pytest.raises(SevenDTDAuthenticationError):
        await create_mosaic(
            FakeClient(namespace),  # type: ignore[arg-type]
            zoom=1,
            a_values=[0],
            b_values=[0],
            output=output,
            manifest=manifest,
            annotate=False,
            cache_token=None,
            concurrency=1,
        )
    assert not output.exists()
    assert not manifest.exists()


@pytest.mark.asyncio
async def test_mosaic_serializes_both_artifacts_before_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    namespace = FakeMap({(0, 0): png_bytes((0, 0, 0, 255))})
    output, manifest = tmp_path / "mosaic.png", tmp_path / "manifest.json"

    def fail_dump(*args: object, **kwargs: object) -> None:
        raise OSError("manifest serialization failed")

    monkeypatch.setattr(map_tools.json, "dump", fail_dump)
    with pytest.raises(OSError, match="manifest serialization"):
        await create_mosaic(
            FakeClient(namespace),  # type: ignore[arg-type]
            zoom=1,
            a_values=[0],
            b_values=[0],
            output=output,
            manifest=manifest,
            annotate=False,
            cache_token=None,
            concurrency=1,
        )
    assert not output.exists()
    assert not manifest.exists()
    assert_directory_empty(tmp_path)
