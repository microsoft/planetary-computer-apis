import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.integration
async def test_config_token_endpoint(client: AsyncClient) -> None:
    response = await client.get("/config/map/token")
    # We expect this path to be not found
    assert response.status_code == 404
