# Architecture

Dependency direction:

```text
CLI -> AsyncSevenDTDClient -> resource namespaces -> HTTP/SSE transport
                              |-> public domain models
```

Transport owns credentials, HTTP status handling, JSON/byte/SSE mechanics, and safe request
diagnostics. Resource namespaces own endpoint paths and conversion from envelopes to domain
aggregates. The CLI owns presentation and file output. Core modules never import CLI, Pillow,
FastAPI, React, persistence, or deployment concerns.

`AsyncSevenDTDClient` owns its internally created `httpx.AsyncClient`. An injected client remains
caller-owned unless ownership is explicitly transferred.

Unknown inbound fields remain available. Required fields demonstrated by captured responses stay
required. Upstream `meta.serverTime` becomes each aggregate's `observed_at`.

Raw map coordinates remain `coord_a` and `coord_b`. The pure projection module implements only the
world-to-tile and tile-bounds transform proven for game `V 3.1.0 (b14)`, dashboard evidence
`22c85370`, tile size 128, and native zooms 0–4. The map resource checks live configuration before
returning that projection. Pixel conversion remains unavailable.

Item and entity-class catalogs are independent read-only resources. They are excluded from current
state snapshots because they are large catalogs rather than volatile server state. Typed
administrative builders remain deterministic; CLI workflows may perform catalog preflight before
executing a prepared mutation. Server-side item search delegates the verified `li` prepared command
through `CommandsNamespace`; entity-class search filters the existing catalog locally.

Verified broadcast and private-message helpers also use prepared commands. Console text quoting is
centralized in pure builders; commands whose quoting or lifecycle behavior remains unobserved stay
unavailable instead of inheriting assumptions from another command.

Ban lifecycle methods preserve raw command results. Unban uses one cross-platform combined identity;
the library does not treat upstream removal wording as proof that an entry existed or was removed.
