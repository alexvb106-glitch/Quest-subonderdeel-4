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
    # Geen tekenpositie als "veldnaam" in de boodschap
    assert response.json()["fout"]["boodschap"] == "De invoer is ongeldig: ongeldige JSON."


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


# Breker S0.3: controletekens (null byte, escape-code, regeleinde) in tekstvelden worden geweigerd
@pytest.mark.parametrize(
    "body",
    [
        pytest.param({"building_referentie": "\x00"}, id="alleen-null-byte"),
        pytest.param({"building_referentie": "pand\x00-1"}, id="null-byte-midden"),
        pytest.param({"building_referentie": "pand\x1b[31m-1"}, id="escape-code"),
        pytest.param({"adres": {**ADRES, "straat": "Hoofd\nstraat"}}, id="regeleinde-in-adres"),
    ],
)
def test_control_characters_return_422(client, auth_headers, body):
    response = client.post("/tekening", json=body, headers=auth_headers)
    assert_error(response, 422, "ongeldige_invoer")
    assert "controle" in response.json()["fout"]["boodschap"]


# Breker S0.3: unicode en emoji zonder controletekens blijven gewoon toegestaan
def test_unicode_text_is_accepted(client, auth_headers):
    body = {"adres": {**ADRES, "straat": "Ĳsselstraat \U0001F3E0", "plaats": "'s-Hertogenbosch"}}
    response = client.post("/tekening", json=body, headers=auth_headers)
    assert response.status_code == 202


# Breker S0.3: een extreem lange onbekende veldnaam wordt niet volledig teruggestuurd
def test_long_unknown_field_name_is_truncated(client, auth_headers):
    body = {"building_referentie": "pand-1", "k" * 100_000: 1}
    response = client.post("/tekening", json=body, headers=auth_headers)
    assert_error(response, 422, "ongeldige_invoer")
    assert len(response.text) < 500


# Breker S0.3: duizenden onbekende velden geven een korte boodschap met alleen een telling
def test_many_unknown_fields_are_summarized(client, auth_headers):
    body = {"building_referentie": "pand-1", **{f"veld{i}": 1 for i in range(5000)}}
    response = client.post("/tekening", json=body, headers=auth_headers)
    assert_error(response, 422, "ongeldige_invoer")
    assert len(response.text) < 1000
    assert "en nog 4995 andere fout(en)" in response.json()["fout"]["boodschap"]


# Breker S0.3: controletekens in een onbekende veldnaam worden niet teruggekaatst
def test_unknown_field_name_with_control_characters_is_sanitized(client, auth_headers):
    response = client.post(
        "/tekening",
        content=rb'{"building_referentie": "pand-1", "a\u0000\u001b[31m": 1}',
        headers={**auth_headers, "Content-Type": "application/json"},
    )
    assert_error(response, 422, "ongeldige_invoer")
    boodschap = response.json()["fout"]["boodschap"]
    assert "\x00" not in boodschap and "\x1b" not in boodschap


# Breker S0.3: onleesbare body (ongeldige UTF-8, extreem diep geneste JSON) geeft een
# 400 in het eigen formaat met een eigen code, geen crash
@pytest.mark.parametrize(
    "content",
    [
        pytest.param(b'{"building_referentie": "\xff\xfe"}', id="ongeldige-utf8"),
        pytest.param(b"[" * 100_000 + b"]" * 100_000, id="diep-genest"),
    ],
)
def test_unreadable_body_returns_400(client, auth_headers, content):
    response = client.post(
        "/tekening", content=content, headers={**auth_headers, "Content-Type": "application/json"}
    )
    assert_error(response, 400, "ongeldig_verzoek")


# Breker S0.3: multipart-upload (bestandsveld) wordt geweigerd in het eigen formaat, zonder crash
def test_multipart_upload_is_rejected(client, auth_headers):
    response = client.post(
        "/tekening",
        data={"building_referentie": "pand-1"},
        files={"bestanden": ("tekening.pdf", b"%PDF-1.4 kapot", "application/pdf")},
        headers=auth_headers,
    )
    assert_error(response, 422, "ongeldige_invoer")


# Breker S0.3: een grote binaire body wordt geweigerd in het eigen formaat, zonder crash
def test_large_binary_body_is_rejected(client, auth_headers):
    response = client.post(
        "/tekening",
        content=b"\x00\xff" * (5 * 1024 * 1024),
        headers={**auth_headers, "Content-Type": "application/octet-stream"},
    )
    assert_error(response, 422, "ongeldige_invoer")
