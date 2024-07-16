import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_colormap_uppercasing(client: AsyncClient) -> None:
    response = await client.get("/legend/colormap/modis-10A2")
    assert response.status_code == 200
