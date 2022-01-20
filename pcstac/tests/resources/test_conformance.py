from typing import Any, Dict

import pystac
import pytest


def remove_root(stac_object: Dict[str, Any]) -> None:
    links = []
    for link in stac_object["links"]:
        if link["rel"] != "root":
            links.append(link)
    stac_object["links"] = links


@pytest.mark.asyncio
async def test_landing_page(app_client):
    """Test landing page"""
    resp = await app_client.get("/")
    assert resp.status_code == 200
    resp_json = resp.json()
    # expected = {
    #     "id", "stac_extensions", "description", "stac_version", "license",
    #     "summaries", "extent", "links", "title", "keywords", "providers"
    # }
    # result = set(resp_json)
    # assert result == expected

    remove_root(resp_json)
    pystac.Catalog.from_dict(resp_json).validate()

    assert "stac_version" in resp_json

    # Make sure OpenAPI docs are linked
    docs = next(filter(lambda link: link["rel"] == "service-doc", resp_json["links"]))[
        "href"
    ]
    resp = await app_client.get(docs)
    assert resp.status_code == 200

    # Make sure conformance classes are linked
    conf = next(filter(lambda link: link["rel"] == "conformance", resp_json["links"]))[
        "href"
    ]
    resp = await app_client.get(conf)
    assert resp.status_code == 200
