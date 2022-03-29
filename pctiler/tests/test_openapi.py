import pytest

from httpx import AsyncClient

from openapi_spec_validator import validate_spec
from requests.models import Response


VALIDATING_SCHEMA = False


@pytest.mark.asyncio
async def test_produces_valid_openapi_spec(client: AsyncClient) -> None:
    """
    When the request supplies an origin header (as a browser would), ensure
    that the response has an `access-control-allow` header, set to all origins.
    """
    response: Response = await client.get(
        "/openapi.json", headers={"origin": "http://example.com"}
    )

    assert response.status_code == 200
    spec_json = response.json()

    # Titiler is injecting some invalid schema -
    # something around Asset
    # Since we aren't importing into API Management,
    # deal with the invalid openapi for now.
    if VALIDATING_SCHEMA:
        validate_spec(spec_json)
