from typing import List

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--no-integration",
        action="store_true",
        default=False,
        help="don't run integration tests",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "integration: mark as an integration test")


def pytest_collection_modifyitems(
    config: pytest.Config, items: List[pytest.Item]
) -> None:
    if config.getoption("--no-integration"):
        # --no-integration given in cli: skip integration tests
        skip_integration = pytest.mark.skip(
            reason="needs --no-integration option to run"
        )
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
