from fastapi.testclient import TestClient

from pccommon.config.collections import MosaicInfo


def test_get(client: TestClient) -> None:
    response = client.get("/mosaic/info?collection=naip")
    assert response.status_code == 200
    info_dict = response.json()
    mosaic_info = MosaicInfo(**info_dict)
    assert mosaic_info.default_location.zoom == 13
