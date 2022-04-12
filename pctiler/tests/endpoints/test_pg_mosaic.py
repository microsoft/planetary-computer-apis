import pytest
from httpx import AsyncClient

from pccommon.config.collections import MosaicInfo


@pytest.mark.asyncio
async def test_get(client: AsyncClient) -> None:
    response = await client.get("/mosaic/info?collection=naip")
    assert response.status_code == 200
    info_dict = response.json()
    mosaic_info = MosaicInfo(**info_dict)
    assert mosaic_info.default_location.zoom == 13
