from typing import Callable

import pytest


@pytest.mark.asyncio
async def test_queryables(app_client, load_test_data: Callable):
    resp = await app_client.get("/queryables")
    assert resp.status_code == 200
    properties = resp.json()["properties"]
    assert "id" in properties
    assert "datetime" in properties
    assert "naip:year" in properties
    assert "naip:state" in properties


@pytest.mark.asyncio
async def test_collection_queryables(app_client, load_test_data: Callable):
    resp = await app_client.get("/collections/naip/queryables")
    assert resp.status_code == 200
    properties = resp.json()["properties"]
    assert "id" in properties
    assert "datetime" in properties
    assert "naip:year" in properties
    assert "naip:state" in properties


@pytest.mark.asyncio
async def test_collection_queryables_404(app_client, load_test_data: Callable):
    resp = await app_client.get("/collections/does-not-exist/queryables")
    assert resp.status_code == 404
