# TODO

import json
import unittest
from pathlib import Path

import rasterio
from fastapi.testclient import TestClient

from tiler.main import app

client = TestClient(app)
HERE = Path(__file__).parent.absolute()


class TestRoot(unittest.TestCase):
    def test_get(self) -> None:
        with open(HERE / "data-files/naip/collection.json") as f:
            data = json.load(f)

        response = client.get("/vrt", json=data)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/xml"
        ds = rasterio.open(response.content.decode("utf-8"))
        assert ds.shape == (12260, 21370)

    def test_error(self) -> None:
        with open(HERE / "data-files/naip/collection.json") as f:
            data = json.load(f)
        for feature in data["features"]:
            del feature["properties"]["proj:shape"]
            del feature["properties"]["proj:transform"]

        response = client.get("/vrt", json=data)

        self.assertEqual(response.status_code, 400)
