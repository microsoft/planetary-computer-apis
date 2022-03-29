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
