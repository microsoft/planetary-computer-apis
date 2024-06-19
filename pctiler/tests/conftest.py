from typing import List

import pytest
from httpx import ASGITransport, AsyncClient
from pytest import Config, Item, Parser


def pytest_addoption(parser: Parser) -> None:
    parser.addoption(
        "--no-integration",
        action="store_true",
        default=False,
        help="don't run integration tests",
    )


def pytest_configure(config: Config) -> None:
    config.addinivalue_line("markers", "integration: mark as an integration test")


def pytest_collection_modifyitems(config: Config, items: List[Item]) -> None:
    if config.getoption("--no-integration"):
        # --no-integration given in cli: skip integration tests
        skip_integration = pytest.mark.skip(
            reason="needs --no-integration option to run"
        )
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)


@pytest.fixture
async def client() -> AsyncClient:
    from titiler.pgstac.db import close_db_connection, connect_to_db

    from pctiler.main import app

    await connect_to_db(app)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
    await close_db_connection(app)
