from typing import Any, Dict, Tuple

import pytest
from httpx import AsyncClient

from pccommon.config.collections import MosaicInfo

REGISTER_TYPE = Tuple[str, Dict[str, Any]]


@pytest.fixture
async def register_search(client: AsyncClient) -> REGISTER_TYPE:

    cql = {
        "filter-lang": "cql2-json",
        "filter": {
            "op": "and",
            "args": [{"op": "=", "args": [{"property": "collection"}, "naip"]}],
        },
    }
    expected_content_hash = "8b989f86a149628eabfde894fb965982"
    response = await client.post("/mosaic/register", json=cql)
    resp = response.json()

    return (expected_content_hash, resp)


@pytest.mark.asyncio
async def test_mosaic_info(client: AsyncClient) -> None:
    response = await client.get("/mosaic/info?collection=naip")
    assert response.status_code == 200
    info_dict = response.json()
    mosaic_info = MosaicInfo(**info_dict)
    assert mosaic_info.default_location.zoom == 13


@pytest.mark.asyncio
async def test_register(client: AsyncClient, register_search: REGISTER_TYPE) -> None:

    expected_content_hash, register_resp = register_search

    # Test that `searchid` which has been removed in titiler remains in pctiler,
    # and that the search hash remains consistent
    assert register_resp["searchid"] == expected_content_hash
    # Test that the links have had the {tileMatrixSetId} template string removed
    assert len(register_resp["links"]) == 2
    assert register_resp["links"][0]["href"].endswith(
        f"/mosaic/{expected_content_hash}/tilejson.json"
    )
    assert register_resp["links"][1]["href"].endswith(
        f"/mosaic/{expected_content_hash}/WMTSCapabilities.xml"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "route",
    [
        # Legacy path routes
        "mosaic/{searchId}/tiles/{z}/{x}/{y}",
        "mosaic/{searchId}/tiles/{z}/{x}/{y}.{format}",
        "mosaic/{searchId}/tiles/{z}/{x}/{y}@{scale}x",
        "mosaic/{searchId}/tiles/{z}/{x}/{y}@{scale}x.{format}",
        "mosaic/{searchId}/tiles/{tileMatrixSetId}/{z}/{x}/{y}",
        "mosaic/{searchId}/tiles/{tileMatrixSetId}/{z}/{x}/{y}.{format}",
        "mosaic/{searchId}/tiles/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x",
        "mosaic/{searchId}/tiles/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x.{format}",
        # Current path routes
        "mosaic/tiles/{searchId}/{z}/{x}/{y}",
        "mosaic/tiles/{searchId}/{z}/{x}/{y}.{format}",
        "mosaic/tiles/{searchId}/{z}/{x}/{y}@{scale}x",
        "mosaic/tiles/{searchId}/{z}/{x}/{y}@{scale}x.{format}",
        "mosaic/tiles/{searchId}/{tileMatrixSetId}/{z}/{x}/{y}",
        "mosaic/tiles/{searchId}/{tileMatrixSetId}/{z}/{x}/{y}.{format}",
        "mosaic/tiles/{searchId}/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x",
        "mosaic/tiles/{searchId}/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x.{format}",
    ],
)
async def test_mosaic_tile_routes(
    client: AsyncClient, register_search: REGISTER_TYPE, route: str
) -> None:
    """
    For backwards compatibility, support both mosaic/tiles/{searchId} and
    mosaic/{searchId}/tiles routes
    """
    expected_content_hash, _ = register_search

    formatted_route = route.format(
        searchId=expected_content_hash,
        tileMatrixSetId="WebMercatorQuad",
        z=16,
        x=17218,
        y=26838,
        scale=2,
        format="png",
    )
    url = (
        f"/{formatted_route}?asset_bidx=image%7C1%2C2%2C3&assets=image&collection=naip"
    )
    response = await client.get(url)
    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "route",
    [
        "mosaic/{searchId}/tilejson.json",
        "mosaic/{searchId}/{tileMatrixSetId}/tilejson.json",
        "mosaic/{searchId}/WMTSCapabilities.xml",
        "mosaic/{searchId}/{tileMatrixSetId}/WMTSCapabilities.xml",
    ],
)
async def test_tile_metadata_routes(
    client: AsyncClient, register_search: REGISTER_TYPE, route: str
) -> None:
    search_id, _ = register_search

    formatted_route = route.format(
        searchId=search_id, tileMatrixSetId="WebMercatorQuad"
    )
    url = (
        f"/{formatted_route}?asset_bidx=image%7C1%2C2%2C3&assets=image&collection=naip"
    )
    response = await client.get(url)
    assert response.status_code == 200
