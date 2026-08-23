# sevendtd

Async Python integration library and `7dtd` CLI for the web API exposed by a locally
hosted 7 Days to Die dedicated server.

The core package has no CLI, web-framework, persistence, or image-decoding dependency.
Protocol behavior comes from observed responses documented in `docs/upstream-api.md`.
Unknown animal records remain deliberately unclaimed. World-to-tile projection is evidence-backed
for the verified 128-block, native-zoom-0–4 dashboard configuration; pixel conversion remains
unclaimed.

## Install

```bash
uv sync --all-extras --dev
```

## Configure

```bash
export SEVENTDTD_BASE_URL=http://server.example:26980
export SEVENTDTD_TOKEN_NAME=replace-me
export SEVENTDTD_SECRET=replace-me
```

## Use

```python
from sevendtd import AsyncSevenDTDClient, SevenDTDSettings

async with AsyncSevenDTDClient.from_settings(SevenDTDSettings()) as client:
    info = await client.server.info()
    print(info.game_name, info.observed_at)
```

```bash
uv run 7dtd status
uv run 7dtd players --json
uv run 7dtd items stone
uv run 7dtd item-search resourceWood
uv run 7dtd entity-search zombie
uv run 7dtd give 171 terrStone 1 --yes
uv run 7dtd say "Server restart in ten minutes"
uv run 7dtd message 171 "Meet at the trader"
uv run 7dtd kick 171 --reason "CLI moderation test"
uv run 7dtd map locate --x 563.0625 --z -506.78125 --zoom 2
```

Start with the [Python consumer guide](docs/python.md). See `docs/` for architecture, configuration,
CLI, testing, protocol evidence, and map-investigation details. Development changes are summarized
in [CHANGELOG.md](CHANGELOG.md).
