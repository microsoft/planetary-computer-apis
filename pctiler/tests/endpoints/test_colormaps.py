import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_colormap_uppercasing(client: AsyncClient) -> None:
    """
    Test mixed casing colormap_name which matches the original key defined
    (and used in public render-configs)
    """
    params = {
        "collection": "naip",
        "item": "al_m_3008506_nw_16_060_20191118_20200114",
        "assets": "image",
        "asset_bidx": "image|1",
        "colormap_name": "modis-10A2",
    }
    response = await client.get(
        "/item/tiles/WebMercatorQuad/15/8616/13419@1x", params=params
    )
    assert response.status_code == 200
