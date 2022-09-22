import asyncio
import random
from typing import Awaitable, Callable

import pytest
from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse
from httpx import AsyncClient
from starlette.status import HTTP_200_OK, HTTP_504_GATEWAY_TIMEOUT

from pccommon.middleware import timeout_middleware

TIMEOUT_SECONDS = 2
BASE_URL = "http://test"

# Setup test app and endpoints to test middleware on
# ==================================

app = FastAPI()
app.state.service_name = "test"


@app.middleware("http")
async def _timeout_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Add a timeout to all requests."""
    return await timeout_middleware(request, call_next, timeout=TIMEOUT_SECONDS)


# Test endpoint to sleep for a configurable amount of time, which may exceed the
# timeout middleware setting
@app.get("/sleep", response_class=PlainTextResponse)
async def route_for_test(t: int) -> str:
    await asyncio.sleep(t)
    return "Done"


# Test endpoint to sleep and confirm that the task is cancelled after the timeout
@app.get("/cancel", response_class=PlainTextResponse)
async def route_for_cancel_test(t: int) -> str:
    for i in range(t):
        await asyncio.sleep(1)
        if i > TIMEOUT_SECONDS:
            raise Exception("Task should have been cancelled")

    return "Done"


# Test middleware
# ===============


async def success_response(client: AsyncClient, timeout: int) -> None:
    print("making request")
    response = await client.get("/sleep", params={"t": timeout})
    assert response.status_code == HTTP_200_OK
    assert response.text == "Done"


async def timeout_response(client: AsyncClient, timeout: int) -> None:
    response = await client.get("/sleep", params={"t": timeout})
    assert response.status_code == HTTP_504_GATEWAY_TIMEOUT


@pytest.mark.asyncio
async def test_timeout() -> None:
    async with AsyncClient(app=app, base_url=BASE_URL) as client:
        await timeout_response(client, 10)


@pytest.mark.asyncio
async def test_no_timeout() -> None:
    async with AsyncClient(app=app, base_url=BASE_URL) as client:
        await success_response(client, 1)


@pytest.mark.asyncio
async def test_multiple_requests() -> None:
    async with AsyncClient(app=app, base_url=BASE_URL) as client:
        timeout_tasks = []
        for _ in range(100):
            t = TIMEOUT_SECONDS + random.randint(1, 10)
            timeout_tasks.append(asyncio.ensure_future(timeout_response(client, t)))

        await asyncio.gather(*timeout_tasks)

        success_tasks = []
        for _ in range(100):
            t = TIMEOUT_SECONDS - 1
            success_tasks.append(asyncio.ensure_future(success_response(client, t)))

        await asyncio.gather(*success_tasks)


@pytest.mark.asyncio
async def test_request_cancelled() -> None:
    async with AsyncClient(app=app, base_url=BASE_URL) as client:
        await client.get("/cancel", params={"t": 10})
