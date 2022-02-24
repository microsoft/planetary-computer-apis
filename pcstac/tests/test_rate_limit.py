import time
import pytest

from pccommon.constants import HTTP_429_TOO_MANY_REQUESTS


@pytest.mark.asyncio
async def test_rate_limit_collection(app_client):
    pytest.skip("Non-deterministic. Set the rate limit in the config file to test.")
    resp = None
    for _ in range(0, 1001):
        tic = time.perf_counter()
        resp = await app_client.get("/collections/naip")
        toc = time.perf_counter()
        print(f"{toc - tic:.3f}")
        if resp.status_code == HTTP_429_TOO_MANY_REQUESTS:
            break
        else:
            assert resp.status_code == 200

    assert resp.status_code == HTTP_429_TOO_MANY_REQUESTS
