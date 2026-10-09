import pytest
from fastapi.testclient import TestClient

from onderdeel4.config import API_KEY_ENV_VAR
from onderdeel4.main import create_app

# Testwaarde voor de API-key; geen echte sleutel
TEST_API_KEY = "test-sleutel-alleen-voor-tests"


# Verse app per test, en daarmee ook een verse in-memory job-opslag
@pytest.fixture
def app():
    return create_app()


# De job-opslag van de app uit deze test
@pytest.fixture
def job_store(app):
    return app.state.job_store


# Headers met de geldige testsleutel
@pytest.fixture
def auth_headers():
    return {"X-API-Key": TEST_API_KEY}


# Client met een geconfigureerde API-key op de server.
# raise_server_exceptions=False: onverwachte fouten komen als 500-response terug, zoals in productie.
@pytest.fixture
def client(app, monkeypatch):
    monkeypatch.setenv(API_KEY_ENV_VAR, TEST_API_KEY)
    return TestClient(app, raise_server_exceptions=False)


# Client zonder geconfigureerde API-key op de server (env var niet gezet)
@pytest.fixture
def client_without_key(app, monkeypatch):
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    return TestClient(app, raise_server_exceptions=False)


# Controleer dat een response het eigen JSON-foutformaat heeft, met de verwachte status en code
def assert_error(response, status: int, code: str) -> None:
    assert response.status_code == status
    body = response.json()
    assert set(body.keys()) == {"fout"}
    assert set(body["fout"].keys()) == {"status", "code", "boodschap"}
    assert body["fout"]["status"] == status
    assert body["fout"]["code"] == code
    assert isinstance(body["fout"]["boodschap"], str) and body["fout"]["boodschap"]
