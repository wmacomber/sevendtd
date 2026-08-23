"""Map diagnostic image composition."""

import asyncio
import hashlib
import io
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image, ImageDraw, UnidentifiedImageError

from sevendtd.client import AsyncSevenDTDClient
from sevendtd.exceptions import SevenDTDAuthenticationError


@dataclass(slots=True)
class TileManifestEntry:
    zoom: int
    coord_a: int
    coord_b: int
    path: str
    status: str
    media_type: str | None = None
    byte_count: int | None = None
    sha256: str | None = None
    width: int | None = None
    height: int | None = None
    classification: str = "request_failed"
    error_type: str | None = None


def inclusive_range(start: int, end: int) -> list[int]:
    step = 1 if end >= start else -1
    return list(range(start, end + step, step))


def classify_image(image: Image.Image) -> str:
    rgba = image.convert("RGBA")
    extrema = rgba.getchannel("A").getextrema()
    minimum, maximum = extrema
    if not isinstance(minimum, (int, float)) or not isinstance(maximum, (int, float)):
        return "invalid_png"
    alpha_min, alpha_max = float(minimum), float(maximum)
    if alpha_max == 0:
        return "fully_transparent"
    if alpha_min < 255:
        return "partially_transparent"
    return "opaque"


def atomic_save_image(image: Image.Image, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output.parent, suffix=".png", delete=False) as handle:
        temporary = Path(handle.name)
    try:
        image.save(temporary, format="PNG")
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_save_json(value: object, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=output.parent, suffix=".json", mode="w", encoding="utf-8", delete=False
    ) as handle:
        temporary = Path(handle.name)
        json.dump(value, handle, indent=2)
        handle.write("\n")
    try:
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_save_mosaic(
    image: Image.Image,
    document: object,
    output: Path,
    manifest: Path,
) -> None:
    """Fully serialize both artifacts before atomically replacing either destination."""

    output.parent.mkdir(parents=True, exist_ok=True)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=output.parent, suffix=".png", delete=False
    ) as image_handle:
        temporary_image = Path(image_handle.name)
    with tempfile.NamedTemporaryFile(
        dir=manifest.parent, suffix=".json", mode="w", encoding="utf-8", delete=False
    ) as manifest_handle:
        temporary_manifest = Path(manifest_handle.name)
    try:
        image.save(temporary_image, format="PNG")
        with temporary_manifest.open("w", encoding="utf-8") as handle:
            json.dump(document, handle, indent=2)
            handle.write("\n")
        os.replace(temporary_image, output)
        os.replace(temporary_manifest, manifest)
    finally:
        temporary_image.unlink(missing_ok=True)
        temporary_manifest.unlink(missing_ok=True)


async def create_mosaic(
    client: AsyncSevenDTDClient,
    *,
    zoom: int,
    a_values: list[int],
    b_values: list[int],
    output: Path,
    manifest: Path,
    annotate: bool,
    cache_token: str | None,
    concurrency: int,
) -> dict[str, object]:
    config = await client.map.config()
    tile_size = config.map_block_size
    semaphore = asyncio.Semaphore(concurrency)

    async def fetch(a: int, b: int) -> tuple[TileManifestEntry, Image.Image | None]:
        entry = TileManifestEntry(
            zoom=zoom,
            coord_a=a,
            coord_b=b,
            path=f"/map/{zoom}/{a}/{b}.png",
            status="failed",
        )
        try:
            async with semaphore:
                tile = await client.map.tile(
                    zoom=zoom, coord_a=a, coord_b=b, cache_token=cache_token
                )
            entry.media_type = tile.media_type
            entry.byte_count = len(tile.content)
            entry.sha256 = hashlib.sha256(tile.content).hexdigest()
            try:
                with Image.open(io.BytesIO(tile.content)) as opened:
                    opened.load()
                    image = opened.convert("RGBA")
            except (OSError, UnidentifiedImageError):
                entry.classification = "invalid_png"
                entry.error_type = "InvalidPNG"
                return entry, None
            entry.width, entry.height = image.size
            if image.size != (tile_size, tile_size):
                entry.classification = "invalid_png"
                entry.error_type = "UnexpectedDimensions"
                return entry, None
            entry.status = "ok"
            entry.classification = classify_image(image)
            return entry, image
        except SevenDTDAuthenticationError:
            raise
        except Exception as exc:  # diagnostic grid records per-cell failures
            entry.error_type = type(exc).__name__
            return entry, None

    pairs = [(a, b) for b in b_values for a in a_values]
    fetched = await asyncio.gather(*(fetch(a, b) for a, b in pairs))
    canvas = Image.new("RGBA", (len(a_values) * tile_size, len(b_values) * tile_size))
    draw = ImageDraw.Draw(canvas)
    entries: list[TileManifestEntry] = []
    for index, (entry, image) in enumerate(fetched):
        row, column = divmod(index, len(a_values))
        x, y = column * tile_size, row * tile_size
        if image is None:
            draw.rectangle((x, y, x + tile_size - 1, y + tile_size - 1), fill="#7f1d1d")
            draw.line((x, y, x + tile_size - 1, y + tile_size - 1), fill="white", width=2)
            draw.line((x + tile_size - 1, y, x, y + tile_size - 1), fill="white", width=2)
        else:
            canvas.alpha_composite(image, (x, y))
        if annotate:
            label = f"{entry.coord_a},{entry.coord_b}"
            draw.rectangle((x + 2, y + 2, x + 8 * len(label) + 4, y + 16), fill="#000000b0")
            draw.text((x + 4, y + 3), label, fill="white")
        entries.append(entry)

    document: dict[str, object] = {
        "zoom": zoom,
        "a_values": a_values,
        "b_values": b_values,
        "tile_size": tile_size,
        "entries": [asdict(entry) for entry in entries],
    }
    atomic_save_mosaic(canvas, document, output, manifest)
    return document
