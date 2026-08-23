# Testing

Offline suite:

```bash
uv lock --check
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
uv build
```

Default pytest execution disables IP-network sockets with `pytest-socket`; Unix-domain sockets
remain enabled because Python's asyncio event loop requires an internal socket pair. Mock transports
therefore remain usable while accidental HTTP/TCP access fails deterministically.

Read-only live tests require `SEVENTDTD_INTEGRATION_TESTS=1` and explicit inclusion of the
`integration` marker because default pytest configuration excludes it.

Mutating tests additionally require:

```text
SEVENTDTD_MUTATING_TESTS=I_ACKNOWLEDGE_SERVER_MUTATION
pytest --run-mutating
```

Destructive tests additionally require:

```text
SEVENTDTD_DESTRUCTIVE_TESTS=I_ACKNOWLEDGE_SERVER_DESTRUCTION
pytest --run-destructive
```

CI never enables live gates. No automated destructive live test exists through Milestone 4.

CI tests Python 3.12 and 3.13. Its packaging job builds wheel and source distribution, installs the
wheel into a clean Python 3.12 environment, imports core `sevendtd`, and verifies that Typer, Rich,
Pillow, FastAPI, and SQLAlchemy were not installed as core dependencies.

The optional mutating `give` test also requires `SEVENTDTD_TEST_GIVE_ENTITY_ID` and
`SEVENTDTD_TEST_GIVE_ITEM_NAME`. It sends exactly one item and only runs when the general mutation
gate and `--run-mutating` are both enabled.
