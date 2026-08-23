"""Map configuration, raw PNG tiles, and verified projection access."""

from sevendtd.exceptions import SevenDTDAPIError, SevenDTDMapTileError
from sevendtd.models.map import MapConfig, MapConfigData, MapTile, RawTileCoordinate
from sevendtd.projection import MapProjection, MapProjectionSpec
from sevendtd.transport.http import HTTPTransport

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class MapNamespace:
    def __init__(self, transport: HTTPTransport) -> None:
        self._transport = transport

    async def config(self) -> MapConfig:
        data, meta = await self._transport.request_json(
            "GET", "/api/map/config", MapConfigData, resource="map.config"
        )
        return MapConfig(**data.model_dump(), observed_at=meta.server_time)

    async def tile(
        self,
        *,
        zoom: int,
        coord_a: int,
        coord_b: int,
        cache_token: str | int | None = None,
    ) -> MapTile:
        coordinate = RawTileCoordinate(zoom=zoom, coord_a=coord_a, coord_b=coord_b)
        endpoint = f"/map/{zoom}/{coord_a}/{coord_b}.png"
        params = {"t": cache_token} if cache_token is not None else None
        try:
            response = await self._transport.request_bytes(
                endpoint, resource="map.tile", params=params
            )
        except SevenDTDAPIError as exc:
            raise SevenDTDMapTileError(
                f"tile request failed for {endpoint} (HTTP {exc.status_code})"
            ) from exc
        content = response.content
        media_type = response.headers.get("content-type")
        if not content:
            raise SevenDTDMapTileError(f"empty tile response for {endpoint}")
        if not content.startswith(PNG_SIGNATURE):
            raise SevenDTDMapTileError(f"invalid PNG response for {endpoint}")
        if media_type and "image/png" not in media_type.lower():
            raise SevenDTDMapTileError(f"unexpected tile content type for {endpoint}")
        return MapTile(
            coordinate=coordinate,
            content=content,
            media_type=media_type,
            content_length=len(content),
            etag=response.headers.get("etag"),
            last_modified=response.headers.get("last-modified"),
        )

    async def projection(self) -> MapProjection:
        config = await self.config()
        if config.map_block_size != 128 or config.max_zoom != 4:
            raise SevenDTDMapTileError(
                "map projection is unsupported for "
                f"mapBlockSize={config.map_block_size}, maxZoom={config.max_zoom}"
            )
        return MapProjection(
            MapProjectionSpec(
                tile_size=config.map_block_size,
                minimum_zoom=0,
                maximum_zoom=config.max_zoom,
                map_size_x=config.map_size.x,
                map_size_y=config.map_size.y,
                map_size_z=config.map_size.z,
            )
        )
