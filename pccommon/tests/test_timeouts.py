import asyncio
from typing import Any

import pytest
from fastapi import FastAPI

from httpx import ASGITransport, AsyncClient
from starlette.status import HTTP_504_GATEWAY_TIMEOUT

from pccommon.middleware import add_timeout

TIMEOUT_SECONDS = 2
BASE_URL = "http://test"


@pytest.mark.asyncio
async def test_add_timeout() -> None:

    # Setup test app and endpoints to test middleware on
    # ==================================

    app = FastAPI()
    app.state.service_name = "test"

    @app.get("/asleep")
    async def asleep() -> Any:
        await asyncio.sleep(1)
        return {}

    # Run this after registering the routes
    add_timeout(app, timeout_seconds=0.001)

    async with AsyncClient(
        transport=ASGITransport(app=app),  # type: ignore
        base_url=BASE_URL,
    ) as client:
        response = await client.get("/asleep")

    assert response.status_code == HTTP_504_GATEWAY_TIMEOUT
