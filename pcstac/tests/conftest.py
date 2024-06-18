import asyncio
import json
import os
import time
from typing import AsyncGenerator, Callable, Dict

import asyncpg
import pytest
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from httpx import ASGITransport, AsyncClient
from pypgstac.db import PgstacDB
from pypgstac.migrate import Migrate
from stac_fastapi.api.models import create_get_request_model, create_post_request_model
from stac_fastapi.pgstac.config import Settings
from stac_fastapi.pgstac.db import close_db_connection, connect_to_db

from pccommon.logging import ServiceName
from pccommon.redis import connect_to_redis
from pcstac.api import PCStacApi
from pcstac.client import PCClient
from pcstac.config import EXTENSIONS, TILER_HREF_ENV_VAR
from pcstac.search import PCSearch, PCSearchGetRequest

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# Setting this environment variable to ensure links are properly constructed
os.environ[TILER_HREF_ENV_VAR] = "http://localhost:8080/data/"

# Testing is set to false because creating/updating via the API is not desirable
#  thus, we actually want to use the migrations and data loaded in via the setup
#  script which builds PQE docker containers
settings = Settings(testing=False)


@pytest.fixture(scope="session")
def event_loop():
    return asyncio.get_event_loop()


@pytest.fixture(scope="session")
async def pqe_pg():
    print(f"Connecting to write database {settings.reader_connection_string}")
    print("writer conn string", settings.reader_connection_string)
    conn = await asyncpg.connect(dsn=settings.reader_connection_string)
    val = await conn.fetchval("SELECT true;")
    print(val)
    await conn.close()

    db = PgstacDB(dsn=settings.reader_connection_string)
    migrator = Migrate(db)
    version = migrator.run_migration()
    db.close()
    print(f"PGStac Migrated to {version}")

    yield settings.reader_connection_string
    await conn.close()


@pytest.fixture(scope="session")
def api_client(pqe_pg):
    print("creating client with settings", settings, settings.reader_connection_string)
    search_get_request_model = create_get_request_model(
        EXTENSIONS, base_model=PCSearchGetRequest
    )
    search_post_request_model = create_post_request_model(
        EXTENSIONS, base_model=PCSearch
    )
    api = PCStacApi(
        title="test title",
        description="test description",
        api_version="1.0.0",
        settings=Settings(debug=True),
        client=PCClient.create(
            post_request_model=search_post_request_model,
        ),
        extensions=EXTENSIONS,
        app=FastAPI(root_path="/stac", default_response_class=ORJSONResponse),
        search_get_request_model=search_get_request_model,
        search_post_request_model=search_post_request_model,
    )

    app: FastAPI = api.app
    app.state.service_name = ServiceName.STAC
    return api


@pytest.mark.asyncio
@pytest.fixture(scope="session")
async def app(api_client) -> AsyncGenerator[FastAPI, None]:
    time.time()
    app: FastAPI = api_client.app
    await connect_to_db(app)
    await connect_to_redis(app)

    yield app

    await close_db_connection(app)


@pytest.mark.asyncio
@pytest.fixture(scope="session")
async def app_client(app) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test/stac",
        headers={"X-Forwarded-For": "127.0.0.1"},
    ) as c:
        yield c


@pytest.fixture
def load_test_data() -> Callable[[str], Dict]:
    def load_file(filename: str) -> Dict:
        with open(os.path.join(DATA_DIR, filename)) as file:
            return json.load(file)

    return load_file
