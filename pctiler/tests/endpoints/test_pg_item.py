import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_item(client: AsyncClient) -> None:
    response = await client.get(
        "/item/info?collection=naip&item=al_m_3008501_ne_16_060_20191109_20200114"
    )
    assert response.status_code == 200

    response = await client.get(
        "/item/assets?collection=naip&item=al_m_3008501_ne_16_060_20191109_20200114"
    )
    assert response.status_code == 200
    assert response.json() == ["image"]


@pytest.mark.asyncio
async def test_item_preview_xss(client: AsyncClient) -> None:
    xss = "%27});alert('xss injected');//</script>"

    item_id = "al_m_3008501_ne_16_060_20191109_20200114"
    item_id_xss = f"{item_id}{xss}"

    response_xss = await client.get(f"/item/map?collection=naip&item={item_id_xss}")

    # The XSS should be sanitized out of the response
    assert response_xss.status_code == 200
    assert "//</script>" not in response_xss.text


@pytest.mark.asyncio
async def test_item_crop(client: AsyncClient) -> None:
    """
    Test the legacy /crop endpoint which is provided by pctiler, backed by the
    /feature endpoint function from titiler-core
    """
    params = {
        "collection": "naip",
        "item": "al_m_3008506_nw_16_060_20191118_20200114",
        "assets": "image",
        "asset_bidx": "image|1",
    }
    geom = {
        "type": "Feature",
        "properties": {},
        "geometry": {
            "coordinates": [
                [
                    [-85.34600303041255, 30.97430719427659],
                    [-85.34600303041255, 30.9740750264651],
                    [-85.34403025022365, 30.9740750264651],
                    [-85.34403025022365, 30.97430719427659],
                    [-85.34600303041255, 30.97430719427659],
                ]
            ],
            "type": "Polygon",
        },
    }

    resp = await client.post("/item/crop.tif", params=params, json=geom)

    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "image/tiff; application=geotiff"
