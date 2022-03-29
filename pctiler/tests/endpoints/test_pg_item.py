from fastapi.testclient import TestClient


def test_item(client: TestClient) -> None:
    response = client.get("/item/info?collection=naip&item=al_m_3008501_ne_16_060_20191109_20200114")
    assert response.status_code == 200

    response = client.get("/item/assets?collection=naip&item=al_m_3008501_ne_16_060_20191109_20200114")
    assert response.status_code == 200
    assert response.json() == ["image"]
