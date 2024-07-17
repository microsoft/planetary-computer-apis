import pytest
from httpx import AsyncClient

from pccommon.config.collections import MosaicInfo


@pytest.mark.asyncio
async def test_get(client: AsyncClient) -> None:
    response = await client.get("/mosaic/info?collection=naip")
    assert response.status_code == 200
    info_dict = response.json()
    mosaic_info = MosaicInfo(**info_dict)
    assert mosaic_info.default_location.zoom == 13


@pytest.mark.asyncio
async def test_register(client: AsyncClient) -> None:
    cql = {
        "filter-lang": "cql2-json",
        "filter": {
            "op": "and",
            "args": [{"op": "=", "args": [{"property": "collection"}, "naip"]}],
        },
    }
    expected_content_hash = "8b989f86a149628eabfde894fb965982"
    response = await client.post("/mosaic/register", json=cql)
    assert response.status_code == 200
    resp = response.json()

    # Test that `searchid` which has been removed in titiler remains in pctiler,
    # and that the search hash remains consistent
    assert resp["searchid"] == expected_content_hash
