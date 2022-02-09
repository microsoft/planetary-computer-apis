from fastapi.testclient import TestClient


def test_get(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "Planetary Developer!"}


def test_ping_no_param(client: TestClient) -> None:
    """
    Test ping endpoint with a mocked client.
    """
    res = client.get("/_mgmt/ping")
    assert res.status_code == 200
    assert res.json() == {"message": "PONG"}
