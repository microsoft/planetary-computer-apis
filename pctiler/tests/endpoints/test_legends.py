import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_classmap(client: AsyncClient) -> None:
    response = await client.get("/legend/classmap/io-lulc")
    assert response.status_code == 200
    classmap = response.json()
    assert classmap["0"] == [0, 0, 0, 0]


@pytest.mark.asyncio
async def test_trim_classmap(client: AsyncClient) -> None:
    response = await client.get("/legend/classmap/io-lulc")
    classmap = response.json()

    keys = list(classmap.keys())
    key_start = keys[0]
    key_end = keys[len(keys) - 1]

    # Trim the first and last entry from the classmap
    response = await client.get("/legend/classmap/io-lulc?trim_start=1&trim_end=1")
    classmap = response.json()

    assert key_start not in classmap
    assert key_end not in classmap


@pytest.mark.asyncio
async def test_get_colormap(client: AsyncClient) -> None:
    response = await client.get("/legend/colormap/jrc-seasonality")
    assert response.status_code == 200
