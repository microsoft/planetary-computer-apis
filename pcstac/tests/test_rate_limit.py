import time

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from pccommon.constants import HTTP_429_TOO_MANY_REQUESTS


@pytest.mark.asyncio
async def test_rate_limit_collection(app: FastAPI):
    pytest.skip("Non-deterministic. Set the rate limit in the config file to test.")

    # set the ip to one that doesn't have the rate limit exception
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"X-Forwarded-For": "127.0.0.2"},
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


@pytest.mark.asyncio
async def test_reregistering_rate_limit_script(app: FastAPI, app_client: AsyncClient):
    # set the ip to one that doesn't have the rate limit exception
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"X-Forwarded-For": "127.0.0.2"},
    ) as app_client:

        async def _hash_exists():
            exists = await app.state.redis.script_exists(
                app.state.redis_rate_limit_script_hash
            )
            return exists[0]

        # Script is registered and requests should succeed
        assert await _hash_exists()
        resp = await app_client.get("/collections/naip/items")
        assert resp.status_code == 200

        # Simulate scenario when all scripts are flushed from the redis script cache
        await app.state.redis.script_flush()
        assert await _hash_exists() is False

        # Request with unregistered script should succeed and re-register the script
        resp = await app_client.get("/collections/naip/items")
        assert resp.status_code == 200
        assert await _hash_exists()
