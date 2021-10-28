import unittest

from fastapi.testclient import TestClient

from tiler.main import app

client = TestClient(app)


class TestRoot(unittest.TestCase):
    def test_get(self) -> None:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"Hello": "Planetary Developer!"}
