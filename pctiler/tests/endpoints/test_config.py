import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.integration
async def test_config_token_endpoint(client: AsyncClient) -> None:
    response = await client.get("/config/map/token")
    assert response.status_code == 200
    assert response.json()["token"]
