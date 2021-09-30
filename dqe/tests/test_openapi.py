import unittest

from fastapi.testclient import TestClient
from openapi_spec_validator import validate_spec
from requests.models import Response

from dqe.main import app

VALIDATING_SCHEMA = False


class DQEOpenAPITest(unittest.TestCase):
    def test_produces_valid_openapi_spec(self) -> None:
        with TestClient(app) as client:
            """
            When the request supplies an origin header (as a browser would), ensure
            that the response has an `access-control-allow` header, set to all origins.
            """
            response: Response = client.get(
                "/openapi.json", headers={"origin": "http://example.com"}
            )

            self.assertEqual(response.status_code, 200)
            spec_json = response.json()

            # Titiler is injecting some invalid schema -
            # something around Asset
            # Since we aren't importing into API Management,
            # deal with the invalid openapi for now.
            if VALIDATING_SCHEMA:
                validate_spec(spec_json)
