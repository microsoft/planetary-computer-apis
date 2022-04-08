import pytest

from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "Planetary Developer!"}


@pytest.mark.asyncio
async def test_ping_no_param(client: AsyncClient) -> None:
    """
    Test ping endpoint with a mocked client.
    """
    res = await client.get("/_mgmt/ping")
    assert res.status_code == 200
    assert res.json() == {"message": "PONG"}
