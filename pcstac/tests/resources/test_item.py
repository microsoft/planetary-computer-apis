import json
from datetime import timedelta
from typing import Callable, Dict
from urllib.parse import parse_qs, urlparse

import pystac
import pytest
from geojson_pydantic.geometries import Polygon
from stac_fastapi.pgstac.models.links import CollectionLinks
from stac_pydantic.shared import UtcDatetime
from starlette.requests import Request
from pydantic import TypeAdapter

from pcstac.config import get_settings

# Use a TypeAdapter to parse any datetime strings in a consistent manner
UtcDatetimeAdapter = TypeAdapter(UtcDatetime)
DATETIME_RFC339 = "%Y-%m-%dT%H:%M:%S.%fZ"


@pytest.mark.asyncio
async def test_get_collection(app_client, load_test_data: Callable):
    resp = await app_client.get("/collections")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_fetches_valid_item(app_client):
    collections_resp = await app_client.get("/collections")
    assert collections_resp.status_code == 200
    first_coll = collections_resp.json()["collections"][0]
    coll_id = first_coll["id"]

    items_resp = await app_client.get(f"/collections/{coll_id}/items")
    first_item = items_resp.json()["features"][0]
    item_id = first_item["id"]

    item_resp = await app_client.get(f"/collections/{coll_id}/items/{item_id}")
    print("WHAT IS THIS", f"/collections/{coll_id}/items/{item_id}", item_resp.json())
    assert item_resp.status_code == 200
    item_dict = item_resp.json()
    # Mock root to allow validation
    mock_root = pystac.Catalog(
        id="test", description="test desc", href="https://example.com"
    )
    item = pystac.Item.from_dict(item_dict, preserve_dict=False, root=mock_root)
    print("ITEM DICT", item_dict)
    item.validate()


@pytest.mark.asyncio
async def test_get_collection_items(app_client):
    collections_resp = await app_client.get("/collections")
    assert collections_resp.status_code == 200
    first_coll = collections_resp.json()["collections"][0]
    coll_id = first_coll["id"]

    items_resp = await app_client.get(f"/collections/{coll_id}/items")
    items = items_resp.json()["features"]

    for item_idx in range(len(items)):
        item = items_resp.json()["features"][item_idx]
        item_id = item["id"]
        print("ITEM", item)
        print("ITEM IDX", item_idx)
        print("COLL ID", coll_id)
        print("ITEM ID", item_id)
        resp = await app_client.get(f"/collections/{coll_id}/items/{item_id}")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_item_search_by_id_post(app_client):
    """Test POST search by item id (core)"""
    ids = ["al_m_3008506_nw_16_060_20191118_20200114"]

    params = {"collections": ["naip"], "ids": ids}
    resp = await app_client.post("/search", json=params)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert len(resp_json["features"]) == len(ids)
    assert set([feat["id"] for feat in resp_json["features"]]) == set(ids)


@pytest.mark.asyncio
async def test_item_search_by_id_no_results_post(app_client):
    """Test POST search by item id (core) when there are no results"""
    search_ids = ["nonexistent_id"]

    params = {"collections": ["naip"], "ids": search_ids}
    resp = await app_client.post("/search", json=params)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert len(resp_json["features"]) == 0


@pytest.mark.asyncio
async def test_item_search_spatial_query_post(app_client):
    """Test POST search with spatial query (core)"""
    items_resp = await app_client.get("/collections/naip/items")
    assert items_resp.status_code == 200

    first_item = items_resp.json()["features"][0]
    item_geom = first_item["geometry"]
    item_id = first_item["id"]

    params = {
        "collections": ["naip"],
        "intersects": item_geom,
    }
    resp = await app_client.post("/search", json=params)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert resp_json["features"][0]["id"] == item_id


@pytest.mark.asyncio
async def test_item_search_temporal_query_post(app_client):
    """Test POST search with single-tailed spatio-temporal query (core)"""
    items_resp = await app_client.get("/collections/naip/items")
    assert items_resp.status_code == 200

    first_item = items_resp.json()["features"][0]
    item_date = UtcDatetimeAdapter.validate_strings(
        first_item["properties"]["datetime"]
    )
    item_date = item_date + timedelta(seconds=1)

    params = {
        "collections": [first_item["collection"]],
        "intersects": first_item["geometry"],
        "datetime": item_date.strftime(DATETIME_RFC339),
    }

    resp = await app_client.post("/search", json=params)

    resp_json = resp.json()
    assert len(resp_json["features"]) == 0


@pytest.mark.asyncio
async def test_item_search_temporal_window_post(app_client):
    """Test POST search with two-tailed spatio-temporal query (core)"""
    items_resp = await app_client.get("/collections/naip/items")
    assert items_resp.status_code == 200

    first_item = items_resp.json()["features"][0]
    item_date = UtcDatetimeAdapter.validate_strings(
        first_item["properties"]["datetime"]
    )
    item_date_before = item_date - timedelta(seconds=1)
    item_date_after = item_date + timedelta(seconds=1)

    params = {
        "collections": [first_item["collection"]],
        "intersects": first_item["geometry"],
        "datetime": f"{item_date_before.strftime(DATETIME_RFC339)}/"
        f"{item_date_after.strftime(DATETIME_RFC339)}",
    }
    resp = await app_client.post("/search", json=params)
    resp_json = resp.json()
    assert resp_json["features"][0]["id"] == first_item["id"]


@pytest.mark.asyncio
async def test_item_search_temporal_window_post_date_only(app_client):
    """Test POST search with spatio-temporal query (core)"""
    items_resp = await app_client.get("/collections/naip/items")
    assert items_resp.status_code == 200

    first_item = items_resp.json()["features"][0]
    item_date = UtcDatetimeAdapter.validate_strings(
        first_item["properties"]["datetime"]
    )
    item_date_before = item_date - timedelta(days=1)
    item_date_after = item_date + timedelta(days=1)

    params = {
        "collections": [first_item["collection"]],
        "intersects": first_item["geometry"],
        "datetime": f"{item_date_before.strftime('%Y-%m-%d')}/"
        f"{item_date_after.strftime('%Y-%m-%d')}",
    }
    resp = await app_client.post("/search", json=params)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert resp_json["features"][0]["id"] == first_item["id"]


@pytest.mark.asyncio
async def test_item_search_by_id_get(app_client):
    """Test GET search by item id (core)"""
    items_resp = await app_client.get("/collections/naip/items")
    assert items_resp.status_code == 200

    first_item = items_resp.json()["features"][0]
    second_item = items_resp.json()["features"][1]
    third_item = items_resp.json()["features"][2]
    ids = [first_item["id"], second_item["id"], third_item["id"]]

    params = {"collections": "naip", "ids": ",".join(ids)}
    resp = await app_client.get("/search", params=params)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert len(resp_json["features"]) == len(ids)
    assert set([feat["id"] for feat in resp_json["features"]]) == set(ids)


@pytest.mark.asyncio
async def test_item_search_bbox_get(app_client):
    """Test GET search with spatial query (core)"""
    items_resp = await app_client.get("/collections/naip/items")
    assert items_resp.status_code == 200

    first_item = items_resp.json()["features"][0]
    params = {
        "collections": first_item["collection"],
        "bbox": ",".join([str(coord) for coord in first_item["bbox"]]),
    }
    resp = await app_client.get("/search", params=params)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert resp_json["features"][0]["id"] == first_item["id"]


@pytest.mark.asyncio
async def test_item_search_get_without_collections(app_client):
    """Test GET search without specifying collections"""
    items_resp = await app_client.get("/collections/naip/items")
    assert items_resp.status_code == 200

    first_item = items_resp.json()["features"][0]
    params = {
        "bbox": ",".join([str(coord) for coord in first_item["bbox"]]),
    }
    resp = await app_client.get("/search", params=params)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert resp_json["features"][0]["id"] == first_item["id"]


@pytest.mark.asyncio
async def test_item_search_temporal_window_get(app_client):
    """Test GET search with spatio-temporal query (core)"""
    items_resp = await app_client.get("/collections/naip/items")
    assert items_resp.status_code == 200

    first_item = items_resp.json()["features"][0]
    item_date = UtcDatetimeAdapter.validate_strings(
        first_item["properties"]["datetime"]
    )
    item_date_before = item_date - timedelta(seconds=1)
    item_date_after = item_date + timedelta(seconds=1)

    params = {
        "collections": first_item["collection"],
        "bbox": ",".join([str(coord) for coord in first_item["bbox"]]),
        "datetime": f"{item_date_before.strftime(DATETIME_RFC339)}/"
        f"{item_date_after.strftime(DATETIME_RFC339)}",
    }
    resp = await app_client.get("/search", params=params)
    resp_json = resp.json()
    assert resp_json["features"][0]["id"] == first_item["id"]


@pytest.mark.asyncio
async def test_item_search_temporal_window_get_date_only(app_client):
    """Test GET search with spatio-temporal query (core)"""
    items_resp = await app_client.get("/collections/naip/items")
    assert items_resp.status_code == 200

    first_item = items_resp.json()["features"][0]
    item_date = UtcDatetimeAdapter.validate_strings(
        first_item["properties"]["datetime"]
    )
    item_date_before = item_date - timedelta(days=1)
    item_date_after = item_date + timedelta(days=1)

    params = {
        "collections": first_item["collection"],
        "bbox": ",".join([str(coord) for coord in first_item["bbox"]]),
        "datetime": f"{item_date_before.strftime('%Y-%m-%d')}/"
        f"{item_date_after.strftime('%Y-%m-%d')}",
    }
    resp = await app_client.get("/search", params=params)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert resp_json["features"][0]["id"] == first_item["id"]


@pytest.mark.asyncio
async def test_item_search_post_without_collection(app_client):
    """Test POST search without specifying a collection"""
    items_resp = await app_client.get("/collections/naip/items")
    assert items_resp.status_code == 200

    first_item = items_resp.json()["features"][0]
    params = {
        "bbox": first_item["bbox"],
    }
    resp = await app_client.post("/search", json=params)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert resp_json["features"][0]["id"] == first_item["id"]


@pytest.mark.asyncio
async def test_item_search_properties_jsonb(app_client):
    """Test POST search with JSONB query (query extension)"""
    items_resp = await app_client.get("/collections/naip/items")
    assert items_resp.status_code == 200

    first_item = items_resp.json()["features"][0]

    # EPSG is a JSONB key
    params = {"query": {"proj:epsg": {"eq": first_item["properties"]["proj:epsg"]}}}
    print(params)
    resp = await app_client.post("/search", json=params)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert len(resp_json["features"]) == 12


@pytest.mark.asyncio
async def test_item_search_get_query_extension(app_client):
    """Test GET search with JSONB query (query extension)"""
    items_resp = await app_client.get("/collections/naip/items")
    assert items_resp.status_code == 200

    first_item = items_resp.json()["features"][0]

    # EPSG is a JSONB key
    params = {
        "collections": [first_item["collection"]],
        "query": json.dumps(
            {"proj:epsg": {"gt": first_item["properties"]["proj:epsg"] + 1}}
        ),
    }
    resp = await app_client.get("/search", params=params)
    # No items found should still return a 200 but with an empty list of features
    assert resp.status_code == 200
    assert len(resp.json()["features"]) == 0

    params["query"] = json.dumps(
        {"proj:epsg": {"eq": first_item["properties"]["proj:epsg"]}}
    )
    resp = await app_client.get("/search", params=params)
    resp_json = resp.json()
    assert len(resp_json["features"]) == 12
    assert (
        resp_json["features"][0]["properties"]["proj:epsg"]
        == first_item["properties"]["proj:epsg"]
    )


@pytest.mark.asyncio
async def test_item_search_get_filter_extension_cql(app_client):
    """Test GET search with JSONB query (cql json filter extension)"""
    items_resp = await app_client.get("/collections/naip/items")
    assert items_resp.status_code == 200

    first_item = items_resp.json()["features"][0]

    # EPSG is a JSONB key
    params = {
        "collections": [first_item["collection"]],
        "filter": {
            "gt": [
                {"property": "proj:epsg"},
                first_item["properties"]["proj:epsg"] + 1,
            ]
        },
    }
    resp = await app_client.post("/search", json=params)
    resp_json = resp.json()

    assert resp.status_code == 200
    assert len(resp_json.get("features")) == 0

    params = {
        "collections": [first_item["collection"]],
        "filter": {
            "eq": [
                {"property": "proj:epsg"},
                first_item["properties"]["proj:epsg"],
            ]
        },
    }
    resp = await app_client.post("/search", json=params)
    resp_json = resp.json()
    assert len(resp_json["features"]) == 12
    assert (
        resp_json["features"][0]["properties"]["proj:epsg"]
        == first_item["properties"]["proj:epsg"]
    )


@pytest.mark.asyncio
async def test_get_missing_item_collection(app_client):
    """Test reading a collection which does not exist"""
    resp = await app_client.get("/collections/invalid-collection/items")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_item_from_missing_item_collection(app_client):
    """Test reading an item from a collection which does not exist"""
    resp = await app_client.get("/collections/invalid-collection/items/some-item")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_pagination_item_collection(app_client):
    """Test item collection pagination links (paging extension)"""

    # Set limit well above actual number of records
    items_resp = await app_client.get("/collections/naip/items?limit=500")
    assert items_resp.status_code == 200

    ids = [item["id"] for item in items_resp.json()["features"]]

    # Paginate through all 13 items with a limit of 1 (expecting 13 requests)
    page = await app_client.get("/collections/naip/items", params={"limit": 1})
    idx = 0
    item_ids = []
    nextThing = None

    while True:
        idx += 1
        page_data = page.json()
        item_ids.append(page_data["features"][0]["id"])
        nextlink = [
            link["href"] for link in page_data["links"] if link["rel"] == "next"
        ]
        if len(nextlink) < 1:
            break
        nextThing = nextlink.pop()
        assert nextThing.startswith("http://test/stac/collections")

        page = await app_client.get(nextThing)
        if idx >= 20:
            assert False

    # limit is 1; we expect the matched number of requests before we run out of pages
    assert idx == len(items_resp.json()["features"])

    # Confirm we have paginated through all items
    assert not set(item_ids) - set(ids)


@pytest.mark.asyncio
async def test_pagination_post(app_client):
    """Test POST pagination (paging extension)"""

    # Set limit well above actual number of records
    items_resp = await app_client.get("/collections/naip/items?limit=500")
    assert items_resp.status_code == 200

    ids = [item["id"] for item in items_resp.json()["features"]]

    # Paginate through all 5 items with a limit of 1 (expecting 5 requests)
    request_body = {"ids": ids, "limit": 1}
    page = await app_client.post("/search", json=request_body)
    idx = 0
    item_ids = []
    while True:
        idx += 1
        page_data = page.json()
        item_ids.append(page_data["features"][0]["id"])
        next_link = list(filter(lambda l: l["rel"] == "next", page_data["links"]))
        if not next_link:
            break
        # Merge request bodies
        request_body.update(next_link[0]["body"])
        page = await app_client.post("/search", json=request_body)

        if idx > 20:
            assert False

    # Confirm we have paginated through all items
    assert not set(item_ids) - set(ids)


@pytest.mark.asyncio
async def test_pagination_token_idempotent(app_client):
    """Test that pagination tokens are idempotent (paging extension)"""

    # Construct a search that should return all items, but limit to a few
    # so that a "next" link is returned
    page = await app_client.get(
        "/search",
        params={"datetime": "1900-01-01T00:00:00Z/2030-01-01T00:00:00Z", "limit": 3},
    )
    assert page.status_code == 200

    # Get the next link
    page_data = page.json()
    next_link = list(filter(lambda l: l["rel"] == "next", page_data["links"]))

    # Confirm token is idempotent
    resp1 = await app_client.get(
        "/search", params=parse_qs(urlparse(next_link[0]["href"]).query)
    )
    resp2 = await app_client.get(
        "/search", params=parse_qs(urlparse(next_link[0]["href"]).query)
    )
    resp1_data = resp1.json()
    resp2_data = resp2.json()

    # Two different requests with the same pagination token should return the same items
    assert [item["id"] for item in resp1_data["features"]] == [
        item["id"] for item in resp2_data["features"]
    ]


@pytest.mark.asyncio
async def test_field_extension_get(app_client):
    """Test GET search with included fields (fields extension)"""
    params = {"fields": "+properties.proj:epsg,+properties.gsd,+collection"}
    resp = await app_client.get("/search", params=params)
    print(resp.json())
    feat_properties = resp.json()["features"][0]["properties"]
    assert not set(feat_properties) - {"proj:epsg", "gsd", "datetime"}


@pytest.mark.asyncio
async def test_field_extension_exclude_default_includes(app_client):
    """Test POST search excluding a forbidden field (fields extension)"""
    body = {"fields": {"exclude": ["geometry"]}}

    resp = await app_client.post("/search", json=body)
    resp_json = resp.json()
    assert "geometry" not in resp_json["features"][0]


@pytest.mark.asyncio
async def test_search_intersects_and_bbox(app_client):
    """Test POST search intersects and bbox are mutually exclusive (core)"""
    bbox = [-118, 34, -117, 35]
    geoj = Polygon.from_bounds(*bbox).model_dump(exclude_none=True)
    params = {"bbox": bbox, "intersects": geoj}
    resp = await app_client.post("/search", json=params)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_get_missing_item(app_client):
    """Test read item which does not exist (transactions extension)"""
    resp = await app_client.get("/collections/naip/items/invalid-item")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_relative_link_construction(app):
    req = Request(
        scope={
            "type": "http",
            "scheme": "http",
            "method": "PUT",
            "root_path": "http://test/stac",
            "path": "/",
            "raw_path": b"/tab/abc",
            "query_string": b"",
            "headers": {},
            "app": app,
        }
    )
    links = CollectionLinks(collection_id="naip", request=req)
    assert links.link_items()["href"] == "http://test/stac/collections/naip/items"


@pytest.mark.asyncio
async def test_tiler_link_construction(app_client):
    """Test that tiler links are constructed correctly"""
    id = "al_m_3008506_nw_16_060_20191118_20200114"

    resp = await app_client.get(f"/collections/naip/items/{id}")
    assert resp.status_code == 200
    resp_json = resp.json()
    links: Dict = resp_json["links"]
    assets: Dict = resp_json["assets"]

    # Get all the links and assets that are expected to have a tiler link
    tile_links = list(filter(lambda link: link["rel"] == "preview", links))
    tile_keys = ["tiles", "overview"]
    tile_assets = list(
        filter(
            lambda asset: (any(key in asset["roles"] for key in tile_keys)),
            assets.values(),
        )
    )

    # Confirm that the tiler based links have the correct base url as the href
    tiler_href = get_settings().tiler_href
    tiler_links = tile_links + tile_assets
    assert len(tiler_links) > 0
    assert all([link["href"].startswith(tiler_href) for link in tiler_links])


@pytest.mark.asyncio
async def test_search_bbox_errors(app_client):
    body = {"query": {"bbox": [0]}}
    resp = await app_client.post("/search", json=body)
    assert resp.status_code == 400

    body = {"query": {"bbox": [100.0, 0.0, 0.0, 105.0, 1.0, 1.0]}}
    resp = await app_client.post("/search", json=body)
    assert resp.status_code == 400

    params = {"bbox": "100.0,0.0,0.0,105.0"}
    resp = await app_client.get("/search", params=params)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_items_page_limits(app_client):
    resp = await app_client.get("/collections/naip/items")
    assert resp.status_code == 200
    resp_json = resp.json()
    assert len(resp_json["features"]) == 10


@pytest.mark.asyncio
async def test_search_get_page_limits(app_client):
    resp = await app_client.get("/search?collection=naip")
    assert resp.status_code == 200
    resp_json = resp.json()
    assert len(resp_json["features"]) == 12


@pytest.mark.asyncio
async def test_search_post_page_limits(app_client):
    params = {"op": "=", "args": [{"property": "collection"}, "naip"]}

    resp = await app_client.post("/search", json=params)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert len(resp_json["features"]) == 12


@pytest.mark.asyncio
async def test_item_search_geometry_collection(app_client):
    """Test POST search by item id (core)"""
    aoi = {
        "type": "GeometryCollection",
        "geometries": [
            {"type": "Point", "coordinates": [-67.67578124999999, 4.390228926463396]},
            {"type": "Point", "coordinates": [-74.619140625, 4.302591077119676]},
            {
                "type": "LineString",
                "coordinates": [
                    [-59.765625, 6.227933930268672],
                    [-63.984375, -2.108898659243126],
                ],
            },
        ],
    }

    params = {"collections": ["naip"], "intersects": aoi}
    resp = await app_client.post("/search", json=params)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_relative_to_absolute_asset_paths(app_client):
    resp = await app_client.get(
        "/collections/naip/items/al_m_3008501_nw_16_060_20191109_20200114"
    )
    assert resp.status_code == 200
    hrefs = [
        link["href"] for link in resp.json()["links"] if link["rel"] == "related-item"
    ]
    assert len(hrefs) > 0
    assert hrefs[0].startswith("http")
