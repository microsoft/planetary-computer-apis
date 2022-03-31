from typing import Any, Dict

import pystac
import pytest

from pcstac.config import STAC_API_VERSION


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
    conformance_link = next(
        filter(lambda link: link["rel"] == "conformance", resp_json["links"])
    )

    assert "conformsTo" in resp_json
    conforms_to = resp_json["conformsTo"]

    # Make sure conformance classes are of the right STAC version
    for conformance_class in conforms_to:
        if "api.stacspec.org" in conformance_class:
            assert STAC_API_VERSION in conformance_class
    resp = await app_client.get(conformance_link["href"])
    assert resp.status_code == 200
