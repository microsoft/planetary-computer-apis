from fastapi.testclient import TestClient


def test_get_classmap(client: TestClient) -> None:
    response = client.get("/legend/classmap/io-lulc")
    assert response.status_code == 200
    classmap = response.json()
    assert classmap["0"] == [0, 0, 0, 0]


def test_get_colormap(client: TestClient) -> None:
    response = client.get("/legend/colormap/jrc-seasonality")
    assert response.status_code == 200
