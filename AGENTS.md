# Repository Agent Guidance

Applies to the entire repository.

## Repository workflow

- Treat `main` as protected. Never commit or push directly to `main`.
- Create a feature branch for every change. Automation-created branches use the `codex/` prefix.
- Publish changes through a pull request. Required checks are `test (3.12)`, `test (3.13)`, and
  `package`; branches must be current with `main` before merge.
- Merge by squash only. Do not create merge commits or rebase-merge pull requests. Delete merged
  branches.
- Force-pushing and deleting `main` are prohibited. The repository ruleset has no bypass actors.
- Zero approving reviews are required while this is a solo-maintainer repository, but all review
  conversations must be resolved. Revisit the approval count before adding collaborators.
- Review Dependabot pull requests before merging, especially major-version updates. Passing CI is
  necessary, not sufficient, evidence of compatibility.
- GitHub Actions must use immutable full commit SHAs. Keep workflow permissions read-only and
  `persist-credentials: false` unless a narrowly scoped change explicitly requires more authority.
- Do not create commits, tags, releases, deployments, or pushes unless the user explicitly asks.

## Project boundaries

- Package version remains `0.4.0.dev0` until an explicitly approved release change.
- Preserve public signatures and behavior unless the task explicitly authorizes a breaking change.
- This repository contains the async Python library and CLI. Do not introduce frontend, database,
  web-framework, persistence, or deployment concerns into core.
- Dependency direction is `CLI -> client -> resource namespaces -> HTTP/SSE transport`, with public
  models alongside resource namespaces. Core must not import CLI, Typer, Rich, Pillow, FastAPI,
  SQLAlchemy, React, or deployment code.
- Keep core installable without CLI extras. Clean-wheel verification must continue proving Typer,
  Rich, Pillow, FastAPI, and SQLAlchemy are absent.
- An internally created `httpx.AsyncClient` is library-owned. An injected client remains
  caller-owned unless ownership is explicitly transferred.
- Preserve secret-safe model serialization, errors, logs, manifests, and diagnostics. Never expose
  token names, secrets, authorization values, or credential-bearing URLs.
- Preserve unknown inbound fields. Do not tighten observed upstream models without protocol
  evidence.

## Safety and live operations

- Default tests are offline. `pytest-socket` blocks IP sockets; keep this protection enabled.
- Never run live tests implicitly. Read-only integration tests require
  `SEVENTDTD_INTEGRATION_TESTS=1`, explicit inclusion of the `integration` marker, configured live
  credentials, and socket enablement on only those tests.
- Mutating live tests additionally require `--run-mutating` and
  `SEVENTDTD_MUTATING_TESTS=I_ACKNOWLEDGE_SERVER_MUTATION`.
- Destructive live tests additionally require `--run-destructive` and
  `SEVENTDTD_DESTRUCTIVE_TESTS=I_ACKNOWLEDGE_SERVER_DESTRUCTION`.
- Never execute `save_world` or `shutdown` during automated work. Never infer permission to run raw
  console commands from permission to edit or test code.
- Preserve raw administrative command strings, risk classifications, confirmation policy,
  exception types, and CLI exit codes.

## Behavioral contracts and known quirks

- Machine-mode finite commands write exactly one valid JSON document to unwrapped stdout. Log
  streaming writes one compact JSON object per line. Diagnostics belong exclusively on stderr.
- Status may be partially successful; preserve per-component results and partial-status exit code
  `6`.
- SSE behavior includes framing tolerance, cursor resume rules, cancellation, bounded retry by
  status class, capped jittered backoff, and attempt exhaustion. Avoid reconnecting after explicit
  cancellation.
- Snapshot authentication failures cancel immediately. Other component failures may produce a
  partial result; aggregate strictly after outstanding work completes and sanitize unexpected
  failures.
- Map projection is evidence-backed only for game `V 3.1.0 (b14)`, dashboard evidence `22c85370`,
  tile size 128, and native zooms 0–4. Preserve the version/configuration compatibility gate.
- Do not infer pixel conversion, cache-token semantics, animal shape, or unexplored/out-of-bounds
  tile meaning. These remain documented uncertainties.
- Keep the established world-to-tile formula. Treat transparent, partial, and opaque valid PNGs as
  distinct. Malformed or incorrectly sized PNGs are `invalid_png` failures with placeholders.
- Artifact writes must be atomic. Refuse map-tile overwrite unless explicitly requested; never
  leave incomplete output. Manifests and artifacts must exclude authentication data.
- Administrative generic-help evidence proves command presence only. `get_time`, `save_world`, and
  `shutdown` syntax remains unverified until command-specific live evidence exists.

## Verification

Run the relevant subset while iterating. Before handing off a broad change, run:

```bash
uv lock --check
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest
uv run 7dtd --help
uv run 7dtd map locate --help
uv build
```

Expected default test behavior: 231 passed and 4 live tests deselected. Test-count changes are not
automatically failures, but explain them.

For packaging changes, repeat the clean Python 3.12 wheel install/import and optional-dependency
absence check implemented by the `package` CI job.

## Documentation and workspace hygiene

- Protocol claims require captured evidence or an explicit uncertainty statement. Keep ADRs and
  `docs/upstream-api.md` aligned with behavioral changes.
- Keep public documentation concise. Update `CHANGELOG.md` for user-visible behavior.
- Preserve unrelated user changes, tracked documentation deletions, `.gitignore`, and any
  `localcontext/` files. `localcontext/` is ignored local material and must not be published.
- Do not weaken security gates, projection gates, atomic-write guarantees, or compatibility aliases
  merely to make a test pass.
