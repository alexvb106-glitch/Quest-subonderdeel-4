import uuid

from conftest import assert_error

ADRES = {"straat": "Hoofdstraat", "huisnummer": "12A", "postcode": "3511 AB", "plaats": "Utrecht"}


# POST met building_referentie: 202 met een uuid als job_id en status processing
def test_post_with_building_referentie(client, auth_headers):
    response = client.post(
        "/tekening",
        json={"building_referentie": "NL.IMBAG.Pand.0363100012345678"},
        headers=auth_headers,
    )
    assert response.status_code == 202
    body = response.json()
    assert set(body.keys()) == {"job_id", "status"}
    assert body["status"] == "processing"
    uuid.UUID(body["job_id"])


# POST met adres en voorkeursroute: ook 202
def test_post_with_adres(client, auth_headers):
    response = client.post(
        "/tekening", json={"adres": ADRES, "voorkeursroute": "c"}, headers=auth_headers
    )
    assert response.status_code == 202
    assert response.json()["status"] == "processing"


# De ontvangen invoer wordt in de job-opslag bewaard
def test_post_stores_request_data(client, auth_headers, job_store):
    response = client.post("/tekening", json={"adres": ADRES}, headers=auth_headers)
    job = job_store.get(response.json()["job_id"])
    assert job is not None
    assert job.request_data["adres"] == ADRES
    assert job.status == "processing"


# Elke POST maakt een nieuwe job met een eigen job_id
def test_each_post_creates_new_job(client, auth_headers):
    body = {"building_referentie": "pand-1"}
    first = client.post("/tekening", json=body, headers=auth_headers).json()["job_id"]
    second = client.post("/tekening", json=body, headers=auth_headers).json()["job_id"]
    assert first != second


# GET op een net aangemaakte job: 200, status processing, overige velden null
def test_get_created_job(client, auth_headers):
    job_id = client.post(
        "/tekening", json={"building_referentie": "pand-1"}, headers=auth_headers
    ).json()["job_id"]
    response = client.get(f"/tekening/{job_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {
        "job_id": job_id,
        "status": "processing",
        "tekening_referentie": None,
        "gebruikte_route": None,
        "foutmelding": None,
    }


# GET op een onbekende id: 404 job_niet_gevonden
def test_get_unknown_job(client, auth_headers):
    response = client.get(f"/tekening/{uuid.uuid4()}", headers=auth_headers)
    assert_error(response, 404, "job_niet_gevonden")
