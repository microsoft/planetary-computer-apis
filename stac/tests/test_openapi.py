# import pytest

# from openapi_spec_validator import validate_spec


# @pytest.mark.asyncio
# async def test_produces_valid_openapi_spec(app_client):
#     """
#     When the request supplies an origin header (as a browser would), ensure
#     that the response has an `access-control-allow` header, set to all origins.
#     """
#     response = await app_client.get(
#         "/openapi.json", headers={"origin": "http://example.com"}
#     )

#     print("content", response.content)

#     assert response.status_code == 200
#     spec_json = response.json()

#     validate_spec(spec_json)
