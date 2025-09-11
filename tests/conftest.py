import pytest
from fastapi.testclient import TestClient
from api.app.main import app

@pytest.fixture(scope="session")
def client():
    return TestClient(app)