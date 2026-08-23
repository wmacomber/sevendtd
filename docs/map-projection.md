# Map projection evidence record

## Status

World-to-tile conversion and tile world bounds are verified for:

- Game `V 3.1.0 (b14)`.
- Dashboard bundle SHA-256 `22c85370a43570f19b62f2f6cc24a753bfec6503c0c8c451c4c02d94356b36b1`.
- Dashboard source-map SHA-256 `b5610c71218134c1c884a606596c4fe17794bf23a4700300cd1030d40dee7eb8`.
- `mapBlockSize=128`, native zooms `0–4`, map size `6144×255×6144`.

Sanitized machine-readable observations live in
`tests/fixtures/map/projection-observations.json`. Missing per-observation timestamps are recorded as
`null`; capture campaign occurred on 2026-08-23.

## Source evidence

Shipped dashboard source maps player markers as `lat=world_x`, `lng=world_z`, uses tile size 128 and
maximum native zoom 4, and rewrites Leaflet tile Y to URL coordinate `-y-1`. This produces:

```text
span(zoom) = 128 × 2^(4 - zoom)
coord_a = floor(world_x / span)
coord_b = -floor(-world_z / span) - 1
```

Tile bounds:

```text
x ∈ [coord_a × span, (coord_a + 1) × span)
z ∈ (coord_b × span, (coord_b + 1) × span]
```

## Live confirmation

DevTools identified the loaded tile beneath a test-player marker. API player positions supplied the
actual X/Z values. Teleports changed one axis at a time, crossed positive and negative quadrants,
sampled both sides of zero, tested exact representable boundaries, and held one position across all
five native zooms. Six separate holdouts covered mixed signs and zooms 0–4. Accepted observations
match exactly.

Dashboard player layer refreshes asynchronously. Two clicks returned the preceding position's tile
until page refresh; those samples are excluded. DOM hit testing also cannot establish membership
when a marker renders exactly on, or within a subpixel of, a tile edge. Boundary rules therefore
combine source mathematics with adjacent non-edge samples and exact X=128 and Z=0 captures. No code
special-case compensates for browser rendering.

## Implemented contract

- `MapProjection.span_for_zoom()`
- `MapProjection.world_to_tile()`
- `MapProjection.tile_to_world_bounds()`
- `MapProjection.contains()`
- `await client.map.projection()` with live configuration gate
- `7dtd map locate --x X --z Z --zoom N [--json]`

Raw `coord_a`/`coord_b` tile access remains supported.

## Deferred questions

- World-to-tile pixel conversion and pixel rounding.
- Cache-token freshness semantics.
- Distinction among transparent unexplored, invalid, and out-of-bounds tiles.
- Projection compatibility with other game/dashboard versions or map configurations.
