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


@pytest.mark.asyncio
async def test_all_collections_have_msft_regions(app_client):
    """Test that all collections have msft:region"""
    resp = await app_client.get("/collections")
    assert resp.status_code == 200
    collections = resp.json()["collections"]
    for collection in collections:
        assert "msft:region" in collection
