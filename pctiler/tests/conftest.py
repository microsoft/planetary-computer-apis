import pytest
from fastapi.testclient import TestClient

from pctiler.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
