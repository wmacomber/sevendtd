# Changelog

## Unreleased — 0.4.0.dev0

Development state; no `v0.1.0`–`v0.4.0` release tags are implied.

### Implemented

- Async typed client for server information, statistics, players, entities, commands, logs, map
  resources, tolerant protocol models, and concurrent partial snapshots.
- CLI for observation, catalogs/search, live logs, administrative helpers, raw console access, and
  diagnostic map tile/mosaic output.
- Risk-labelled administration covering item delivery, messages, moderation, ban management, and
  preserved helpers for game time, world save, and shutdown.
- Item and entity-class catalogs plus local and server-side search.
- Evidence-backed world-to-tile projection and bounds for the verified 128-block, native zoom 0–4
  dashboard configuration.
- Offline network protection, Python 3.12/3.13 CI, distribution builds, and clean-wheel core import
  verification.

### Known uncertainties

- Animal records remain opaque until a stable non-empty upstream shape is observed.
- Pixel mapping is not established.
- Map cache-token semantics are not established.
- Unexplored and out-of-bounds tile semantics are not classified.
- Projection remains version/configuration-gated; other server/dashboard versions are unverified.
