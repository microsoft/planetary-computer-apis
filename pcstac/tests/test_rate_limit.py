import time

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from pccommon.constants import HTTP_429_TOO_MANY_REQUESTS


@pytest.mark.asyncio
async def test_rate_limit_collection(app: FastAPI):
    pytest.skip("Non-deterministic. Set the rate limit in the config file to test.")

    # set the ip to one that doesn't have the rate limit exception
    async with AsyncClient(
        app=app, base_url="http://test", headers={"X-Forwarded-For": "127.0.0.2"}
    ) as app_client:
        resp = None
        for _ in range(0, 400):
            tic = time.perf_counter()
            resp = await app_client.get("/collections/naip")
            toc = time.perf_counter()
            print(f"{toc - tic:.3f}")
            if resp.status_code == HTTP_429_TOO_MANY_REQUESTS:
                break
            else:
                assert resp.status_code == 200

        assert resp.status_code == HTTP_429_TOO_MANY_REQUESTS


@pytest.mark.asyncio
async def test_rate_limit_collection_ip_Exception(app_client: AsyncClient):
    for _ in range(0, 400):
        resp = await app_client.get("/collections/naip")
        assert resp.status_code == 200
