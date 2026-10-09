import pytest

from conftest import assert_error
from onderdeel4.routes.tekening import get_job_store

ADRES = {"straat": "Hoofdstraat", "huisnummer": "12", "postcode": "3511 AB", "plaats": "Utrecht"}


# Ongeldige invoer op POST /tekening: altijd 422 ongeldige_invoer in het eigen formaat
@pytest.mark.parametrize(
    "body",
    [
        pytest.param({}, id="leeg-object"),
        pytest.param({"voorkeursroute": "a"}, id="geen-identificatieveld"),
        pytest.param({"building_referentie": "pand-1", "voorkeursroute": "d"}, id="ongeldige-route"),
        pytest.param({"adres": {"straat": "Hoofdstraat", "huisnummer": "12"}}, id="onvolledig-adres"),
        pytest.param({"adres": {**ADRES, "plaats": "   "}}, id="adresveld-alleen-spaties"),
        pytest.param({"building_referentie": "pand-1", "bestanden": ["a.pdf"]}, id="extra-veld-bestanden"),
        pytest.param({"building_referentie": 12345}, id="verkeerd-datatype"),
        pytest.param({"adres": {**ADRES, "huisnummer": 12}}, id="huisnummer-als-getal"),
        pytest.param({"building_referentie": ""}, id="lege-building-referentie"),
        pytest.param({"building_referentie": "x" * 201}, id="te-lange-tekst"),
        pytest.param(["building_referentie"], id="geen-object"),
    ],
)
def test_invalid_body_returns_422(client, auth_headers, body):
    response = client.post("/tekening", json=body, headers=auth_headers)
    assert_error(response, 422, "ongeldige_invoer")


# Helemaal geen body: ook 422 in het eigen formaat
def test_missing_body_returns_422(client, auth_headers):
    response = client.post("/tekening", headers=auth_headers)
    assert_error(response, 422, "ongeldige_invoer")


# Kapotte JSON: ook 422 in het eigen formaat
def test_malformed_json_returns_422(client, auth_headers):
    response = client.post(
        "/tekening",
        content=b"{niet geldig",
        headers={**auth_headers, "Content-Type": "application/json"},
    )
    assert_error(response, 422, "ongeldige_invoer")


# De boodschap noemt het betreffende veld, zodat onderdeel 5 een begrijpelijke melding kan tonen
def test_validation_message_names_field(client, auth_headers):
    response = client.post(
        "/tekening", json={"adres": {"straat": "Hoofdstraat"}}, headers=auth_headers
    )
    assert "adres.postcode" in response.json()["fout"]["boodschap"]


# Onbekend pad: 404 in het eigen formaat
def test_unknown_path_returns_404(client):
    assert_error(client.get("/bestaat-niet"), 404, "niet_gevonden")


# Verkeerde methode: 405 in het eigen formaat
def test_wrong_method_returns_405(client, auth_headers):
    response = client.delete("/tekening", headers=auth_headers)
    assert_error(response, 405, "methode_niet_toegestaan")


# Geforceerde onverwachte fout: 500 interne_fout zonder interne details in de response
def test_unexpected_error_returns_500_without_details(app, client, auth_headers):
    class BrokenJobStore:
        def create(self, request_data):
            raise RuntimeError("geheim intern detail")

    app.dependency_overrides[get_job_store] = lambda: BrokenJobStore()
    response = client.post(
        "/tekening", json={"building_referentie": "pand-1"}, headers=auth_headers
    )
    assert_error(response, 500, "interne_fout")
    assert "geheim intern detail" not in response.text
    assert "RuntimeError" not in response.text
    assert "Traceback" not in response.text
