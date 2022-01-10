import unittest

from fastapi.testclient import TestClient

from pctiler.main import app

client = TestClient(app)


class TestRoot(unittest.TestCase):
    def test_get(self) -> None:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"Hello": "Planetary Developer!"}


class TestHealth(unittest.TestCase):
    def test_ping_no_param(self) -> None:
        """
        Test ping endpoint with a mocked client.
        """
        res = client.get("/_mgmt/ping")
        assert res.status_code == 200
        assert res.json() == {"message": "PONG"}
