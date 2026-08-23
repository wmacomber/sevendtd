# CLI

```text
7dtd status [--json] [--strict]
7dtd players [--json]
7dtd hostiles [--json]
7dtd animals [--json]
7dtd items [QUERY] [--blocks-only] [--json]
7dtd item-search QUERY [--json]
7dtd entity-classes [QUERY] [--json]
7dtd entity-search QUERY [--json]
7dtd give ENTITY_ID ITEM_NAME AMOUNT [--quality 1..6] [--no-validate-item] [--yes] [--json]
7dtd say MESSAGE [--json]
7dtd message ENTITY_ID MESSAGE [--json]
7dtd kick ENTITY_ID [--reason TEXT] [--yes] [--json]
7dtd ban ENTITY_ID DURATION UNIT [--reason TEXT] [--yes] [--json]
7dtd ban-list [--json]
7dtd unban COMBINED_IDENTITY [--yes] [--json]
7dtd command COMMAND [--json] [--yes]
7dtd console
7dtd logs [--json] [--no-reconnect] [--max-retries N]
7dtd map info [--json]
7dtd map tile --zoom N --coord-a A --coord-b B --output FILE
7dtd map locate --x X --z Z --zoom N [--json]
7dtd map mosaic --zoom N --a-start A --a-end A --b-start B --b-end B \
  --output mosaic.png --manifest mosaic.json
```

Finite `--json` output uses snake_case. Streaming log JSON uses one object per line. Raw command
execution requires confirmation unless `--yes`. Tile output refuses replacement unless `--force`.

`map locate` fetches live map configuration, permits verified native zooms `0–4`, and returns the
raw tile coordinate, world-unit span, bounds, edge-inclusivity flags, and projection evidence ID.
Projection requires `mapBlockSize=128` and `maxZoom=4`; raw tile commands remain available for other
configurations. X bounds are `[min_x, max_x)`. Z bounds are `(min_z, max_z]`. Pixel conversion is
not offered.

`give` targets integer entity IDs. It checks `ITEM_NAME` against `/api/item` using an exact,
case-sensitive match before prompting. `--no-validate-item` skips that lookup but retains safe-token,
positive-amount, and quality validation. Quality is restricted to `1–6`. The command remains a
server-authorized mutation; CLI confirmation is not an authorization boundary.

`item-search` sends the verified read-only `li QUERY` console command and returns matching internal
item names without downloading the full catalog. `QUERY` must be one conservative console token;
use `items QUERY` when searching localized names or filtering block metadata. `entity-search` fetches
the entity-class catalog and filters class names case-insensitively because no filtered upstream
entity-class search has been observed.

`say` broadcasts and `message` sends a private message to one entity ID. They execute without a
confirmation prompt. Pass the entire message as one shell argument; the typed builder applies the
game-console quoting established by live observation. Printable Unicode, spaces, and apostrophes
are accepted. Double quotes, backslashes, control characters, surrounding whitespace, and `; | &`
are rejected because their console escaping or separator behavior remains unverified.

`kick` targets an integer entity ID and accepts an optional safely quoted reason. It displays the
target and reason before confirmation unless `--yes` is supplied.

`ban` targets an online integer entity ID, requires a positive duration and one of `minute`, `hour`,
`day`, `week`, `month`, or `year`, and accepts an optional safely quoted reason. It uses an explicit
destructive confirmation unless `--yes` is supplied. `ban-list` returns the raw upstream command
result without confirmation.

`unban` accepts one `players[n].crossplatform_id.combined_string` value, such as an `EOS_...` token.
It does not accept separate platform/user arguments. Upstream reports removal even for an identity
that was not banned, so confirm success with `ban-list` and reconnection. Raw `command` remains
available.

Exit codes: `0` success, `2` usage, `3` configuration/authentication, `4` connection/timeout,
`5` upstream/protocol/command failure, `6` partial snapshot, `130` cancellation.
