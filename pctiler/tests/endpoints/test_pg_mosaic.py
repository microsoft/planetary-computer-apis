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
    response = await client.post("/mosaic/register", json=cql)
    expected_content_hash = response.json()["searchid"]
    resp = response.json()
    return (expected_content_hash, resp)


async def test_register_search_with_geom(client: AsyncClient) -> None:
    geom = {
        "type": "Polygon",
        "coordinates": [
            [
                [-79.09062791441062, 43.08554661560049],
                [-79.0629876337021, 43.08554661560049],
                [-79.0629876337021, 43.067969831431895],
                [-79.09062791441062, 43.067969831431895],
                [-79.09062791441062, 43.08554661560049],
            ]
        ],
    }
    cql = {
        "filter-lang": "cql2-json",
        "filter": {
            "op": "and",
            "args": [
                {"op": "=", "args": [{"property": "collection"}, "naip"]},
                {"op": "s_intersects", "args": [{"property": "geometry"}, geom]},
            ],
        },
    }
    response = await client.post("/mosaic/register", json=cql)
    assert response.status_code == 200
    assert response.json()["searchid"] == "2607eab51afd5d626da8d50d9df3bbf0"


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
    assert len(register_resp["links"]) == 3
    assert register_resp["links"][0]["href"].endswith(
        f"/mosaic/{expected_content_hash}/info"
    )  # gets added by searchInfoExtension
    assert register_resp["links"][1]["href"].endswith(
        f"/mosaic/{expected_content_hash}/tilejson.json"
    )
    assert register_resp["links"][2]["href"].endswith(
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


async def test_info_path_with_searchid(
    client: AsyncClient, register_search: REGISTER_TYPE
) -> None:
    # route source code is in titiler/mosaic/titiler/mosaic/factory.py#L157
    # the searchId functionality is added by titiler-pgstac
    route = "mosaic/{searchId}/info"
    expected_content_hash, _ = register_search
    formatted_route = route.format(searchId=expected_content_hash)
    url = (
        f"/{formatted_route}?asset_bidx=image%7C1%2C2%2C3&assets=image&collection=naip"
    )
    response = await client.get(url)
    assert response.status_code == 200


async def test_info_path_with_bad_searchid(client: AsyncClient) -> None:
    route = "mosaic/{searchId}/info"

    # does not match the one we registered in the fixture
    expected_content_hash = "9b989f86a149628eabfde894fb965982"

    formatted_route = route.format(searchId=expected_content_hash)
    url = (
        f"/{formatted_route}?asset_bidx=image%7C1%2C2%2C3&assets=image&collection=naip"
    )
    response = await client.get(url)
    assert response.status_code == 404


async def test_bad_searchid(client: AsyncClient) -> None:
    route = "mosaic/tiles/{searchId}/{z}/{x}/{y}"

    # does not match the one we registered in the fixture
    expected_content_hash = "9b989f86a149628eabfde894fb965982"

    formatted_route = route.format(
        searchId=expected_content_hash, z=16, x=17218, y=26838
    )
    url = (
        f"/{formatted_route}?asset_bidx=image%7C1%2C2%2C3&assets=image&collection=naip"
    )
    response = await client.get(url)
    assert response.status_code == 404


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
