import pytest

from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_classmap(client: AsyncClient) -> None:
    response = await client.get("/legend/classmap/io-lulc")
    assert response.status_code == 200
    classmap = response.json()
    assert classmap["0"] == [0, 0, 0, 0]


@pytest.mark.asyncio
async def test_get_colormap(client: AsyncClient) -> None:
    response = await client.get("/legend/colormap/jrc-seasonality")
    assert response.status_code == 200
