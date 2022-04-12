import pytest
from httpx import AsyncClient


@pytest.fixture
async def client() -> AsyncClient:
    from titiler.pgstac.db import close_db_connection, connect_to_db

    from pctiler.main import app

    await connect_to_db(app)
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    await close_db_connection(app)
