import json
import pytest
from httpx import AsyncClient

from pctiler.colormaps.lidarusgs import lidar_colormaps
from pctiler.colormaps.lulc import lulc_colormaps


@pytest.mark.asyncio
async def test_get_invalid_interval(client: AsyncClient) -> None:
    response = await client.get("/legend/interval/io-lulc")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_interval(client: AsyncClient) -> None:
    response = await client.get("/legend/interval/lidar-hag")
    assert response.status_code == 200
    interval = response.json()

    # The interval has been serialized/deserialized which can change
    # the sequence type, do the same to the original for comparison
    lidar_json = json.loads(json.dumps(lidar_colormaps["lidar-hag"]))
    assert interval == lidar_json


@pytest.mark.asyncio
async def test_trim_interval(client: AsyncClient) -> None:
    # Trim the first and last entry from the classmap
    response = await client.get("/legend/interval/lidar-hag?trim_start=1&trim_end=1")
    interval = response.json()

    lidar_hag = lidar_colormaps["lidar-hag"]
    assert len(interval) == len(lidar_hag) - 2
    assert interval[0] != lidar_hag[0]
    assert interval[-1] != lidar_hag[-1]


@pytest.mark.asyncio
async def test_get_classmap(client: AsyncClient) -> None:
    response = await client.get("/legend/classmap/io-lulc")
    assert response.status_code == 200
    classmap = response.json()

    # The classmap has been serialized/deserialized which can change
    # the sequence type, do the same to the original for comparison
    lulc_json = json.loads(json.dumps(lulc_colormaps["io-lulc"]))
    assert classmap == lulc_json


@pytest.mark.asyncio
async def test_trim_classmap(client: AsyncClient) -> None:
    response = await client.get("/legend/classmap/io-lulc")
    classmap = response.json()

    keys = list(classmap.keys())
    key_start = keys[0]
    key_end = keys[-1]

    # Trim the first and last entry from the classmap
    response = await client.get("/legend/classmap/io-lulc?trim_start=1&trim_end=1")
    classmap = response.json()

    assert key_start not in classmap
    assert key_end not in classmap


@pytest.mark.asyncio
async def test_get_colormap(client: AsyncClient) -> None:
    response = await client.get("/legend/colormap/jrc-seasonality")
    assert response.status_code == 200
