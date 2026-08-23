import os

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--run-mutating", action="store_true", default=False)
    parser.addoption("--run-destructive", action="store_true", default=False)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    read_enabled = os.getenv("SEVENTDTD_INTEGRATION_TESTS") == "1"
    mutating_enabled = (
        read_enabled
        and os.getenv("SEVENTDTD_MUTATING_TESTS") == "I_ACKNOWLEDGE_SERVER_MUTATION"
        and config.getoption("--run-mutating")
    )
    destructive_enabled = (
        read_enabled
        and os.getenv("SEVENTDTD_DESTRUCTIVE_TESTS") == "I_ACKNOWLEDGE_SERVER_DESTRUCTION"
        and config.getoption("--run-destructive")
    )
    for item in items:
        if "destructive" in item.keywords and not destructive_enabled:
            item.add_marker(pytest.mark.skip(reason="destructive live-test gate not enabled"))
        elif "mutating" in item.keywords and not mutating_enabled:
            item.add_marker(pytest.mark.skip(reason="mutating live-test gate not enabled"))
        elif "integration" in item.keywords and not read_enabled:
            item.add_marker(pytest.mark.skip(reason="read-only live-test gate not enabled"))
