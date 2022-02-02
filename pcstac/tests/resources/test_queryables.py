from typing import Callable

import pytest


@pytest.mark.asyncio
async def test_queryables(app_client, load_test_data: Callable):
    resp = await app_client.get("/queryables")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_collection_queryables(app_client, load_test_data: Callable):
    resp = await app_client.get("/collections/naip/queryables")
    assert resp.status_code == 200
