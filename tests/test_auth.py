import pytest
from fastapi.testclient import TestClient

from conftest import assert_error
from onderdeel4.config import API_KEY_ENV_VAR

VALID_BODY = {"building_referentie": "NL.IMBAG.Pand.0363100012345678"}


# Beide endpoints, zodat elke auth-test voor allebei draait
@pytest.fixture(params=["post", "get"])
def call_endpoint(request):
    def _call(client, headers=None):
        if request.param == "post":
            return client.post("/tekening", json=VALID_BODY, headers=headers)
        return client.get("/tekening/onbekend-id", headers=headers)

    return _call


# Geen header: 401 api_key_ontbreekt
def test_missing_header_is_rejected(client, call_endpoint):
    assert_error(call_endpoint(client), 401, "api_key_ontbreekt")


# Lege header: ook 401 api_key_ontbreekt
def test_empty_header_is_rejected(client, call_endpoint):
    assert_error(call_endpoint(client, {"X-API-Key": ""}), 401, "api_key_ontbreekt")


# Foute sleutel: 401 api_key_ongeldig
def test_wrong_key_is_rejected(client, call_endpoint):
    assert_error(call_endpoint(client, {"X-API-Key": "foute-sleutel"}), 401, "api_key_ongeldig")


# Sleutel met niet-ASCII-tekens: netjes 401, geen interne fout
def test_non_ascii_key_is_rejected(client, call_endpoint):
    headers = {"X-API-Key": "sleutel-é".encode("utf-8")}
    assert_error(call_endpoint(client, headers), 401, "api_key_ongeldig")


# Env var niet gezet op de server: fail closed met 500 api_key_niet_geconfigureerd
def test_unconfigured_key_fails_closed(client_without_key, call_endpoint, auth_headers):
    assert_error(
        call_endpoint(client_without_key, auth_headers), 500, "api_key_niet_geconfigureerd"
    )


# Env var leeg op de server: ook fail closed
def test_empty_configured_key_fails_closed(app, monkeypatch, call_endpoint, auth_headers):
    monkeypatch.setenv(API_KEY_ENV_VAR, "   ")
    client = TestClient(app, raise_server_exceptions=False)
    assert_error(call_endpoint(client, auth_headers), 500, "api_key_niet_geconfigureerd")


# Juiste sleutel: doorgelaten (POST geeft 202, GET op onbekende id geeft 404 i.p.v. 401)
def test_valid_key_is_accepted(client, call_endpoint, auth_headers):
    response = call_endpoint(client, auth_headers)
    assert response.status_code in (202, 404)
    if response.status_code == 404:
        assert_error(response, 404, "job_niet_gevonden")


# Auth gaat voor invoervalidatie: ongeldige invoer zonder sleutel geeft 401, geen 422
def test_auth_is_checked_before_validation(client):
    response = client.post("/tekening", json={"onzin": True})
    assert_error(response, 401, "api_key_ontbreekt")


# De OpenAPI-documentatie is zonder sleutel bereikbaar (aanname 6)
def test_docs_are_public(client_without_key):
    assert client_without_key.get("/openapi.json").status_code == 200
    assert client_without_key.get("/docs").status_code == 200
