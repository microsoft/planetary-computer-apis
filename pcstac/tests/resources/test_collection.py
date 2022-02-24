import json

import pytest


@pytest.mark.asyncio
async def test_get_collections(app_client):
    """Test read /collections"""
    resp = await app_client.get("/collections")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_collection(app_client):
    """Test read a collection which does exist"""
    resp = await app_client.get("/collections/naip")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_collection_not_found(app_client):
    """Test read a collection which does not exist"""
    resp = await app_client.get("/collections/does-not-exist")
    print(json.dumps(resp.json(), indent=2))
    assert resp.status_code == 404
