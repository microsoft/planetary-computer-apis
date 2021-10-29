import unittest

from fastapi.testclient import TestClient

from pcstac.main import app


class TestRoot(unittest.TestCase):
    def test_cors_enabled(self) -> None:
        with TestClient(app) as client:
            """
            When the request supplies an origin header (as a browser would), ensure
            that the response has an `access-control-allow` header, set to all origins.
            """
            expected_header = "access-control-allow-origin"
            response = client.get("/", headers={"origin": "http://example.com"})

            self.assertEqual(response.status_code, 200)
            self.assertIn(expected_header, response.headers)
            self.assertEqual(response.headers[expected_header], "*")
