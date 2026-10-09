import json
import math

import pytest
from pydantic import ValidationError

from onderdeel4.intermediate_format import ExtractionResult, Measurement


# Hulpfunctie: geldige basisgegevens voor één maat, per test aan te passen.
# De waarde 25370 mm komt uit de spike (Naxosdreef); coördinaten en bestandsnamen
# in dit bestand zijn fictief en alleen bedoeld om het formaat te testen.
def make_measurement_data(**overrides) -> dict:
    data = {
        "id": "m1",
        "waarde": 25370.0,
        "positie": {"pagina": 1, "x": 120.5, "y": 340.0, "eenheid": "pt"},
        "richting": "horizontaal",
        "bron": {"type": "vector", "bestand": "naxosdreef.pdf"},
        "betrouwbaarheid": "onzeker",
    }
    data.update(overrides)
    return data


# Geldige maten voor elk brontype: vector (pt), scan (px) en handmatig (zonder positie)
def test_vector_measurement_is_valid():
    measurement = Measurement(**make_measurement_data())
    assert measurement.bron.type == "vector"
    assert measurement.positie.eenheid == "pt"
    assert measurement.eenheid == "mm"


def test_scan_measurement_is_valid():
    measurement = Measurement(
        **make_measurement_data(
            positie={"pagina": 2, "x": 1500, "y": 820, "eenheid": "px"},
            bron={"type": "scan", "bestand": "theemsdreef_scan.pdf"},
        )
    )
    assert measurement.bron.type == "scan"
    assert measurement.positie.eenheid == "px"


def test_manual_measurement_without_position_is_valid():
    measurement = Measurement(
        **make_measurement_data(
            positie=None,
            richting=None,
            bron={
                "type": "handmatig",
                "bestand": "theemsdreef_scan.pdf",
                "toelichting": "handmatig overgetypt van scan",
            },
        )
    )
    assert measurement.positie is None
    assert measurement.richting is None
    assert measurement.bron.toelichting == "handmatig overgetypt van scan"


# Labels: alleen de drie vaste waarden zijn toegestaan
@pytest.mark.parametrize("label", ["onzeker", "ontbreekt", "bewezen"])
def test_known_labels_are_accepted(label):
    overrides = {"betrouwbaarheid": label}
    if label == "ontbreekt":
        overrides["waarde"] = None
    if label == "bewezen":
        overrides["onderbouwing"] = "optelsom deelmaten klopt"
    assert Measurement(**make_measurement_data(**overrides)).betrouwbaarheid == label


@pytest.mark.parametrize("label", ["zeker", "Bewezen", "", None])
def test_unknown_labels_are_rejected(label):
    with pytest.raises(ValidationError):
        Measurement(**make_measurement_data(betrouwbaarheid=label))


# Consistentie tussen label, waarde en onderbouwing
def test_missing_label_with_value_is_rejected():
    with pytest.raises(ValidationError):
        Measurement(**make_measurement_data(betrouwbaarheid="ontbreekt"))


def test_null_value_with_uncertain_label_is_rejected():
    with pytest.raises(ValidationError):
        Measurement(**make_measurement_data(waarde=None, betrouwbaarheid="onzeker"))


def test_null_value_with_proven_label_is_rejected():
    with pytest.raises(ValidationError):
        Measurement(
            **make_measurement_data(
                waarde=None, betrouwbaarheid="bewezen", onderbouwing="controle"
            )
        )


def test_null_value_with_missing_label_is_valid():
    measurement = Measurement(
        **make_measurement_data(waarde=None, betrouwbaarheid="ontbreekt")
    )
    assert measurement.waarde is None


@pytest.mark.parametrize("reason", [None, "", "   "])
def test_proven_without_reason_is_rejected(reason):
    with pytest.raises(ValidationError):
        Measurement(
            **make_measurement_data(betrouwbaarheid="bewezen", onderbouwing=reason)
        )


def test_proven_with_reason_is_valid():
    measurement = Measurement(
        **make_measurement_data(
            betrouwbaarheid="bewezen", onderbouwing="optelsom deelmaten klopt"
        )
    )
    assert measurement.betrouwbaarheid == "bewezen"


# Ongeldige invoer wordt geweigerd
@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_non_finite_value_is_rejected(value):
    with pytest.raises(ValidationError):
        Measurement(**make_measurement_data(waarde=value))


@pytest.mark.parametrize("coordinate", ["x", "y"])
@pytest.mark.parametrize("value", [math.nan, math.inf])
def test_non_finite_coordinate_is_rejected(coordinate, value):
    position = {"pagina": 1, "x": 1.0, "y": 1.0, "eenheid": "pt"}
    position[coordinate] = value
    with pytest.raises(ValidationError):
        Measurement(**make_measurement_data(positie=position))


@pytest.mark.parametrize("page", [0, -1])
def test_page_below_one_is_rejected(page):
    with pytest.raises(ValidationError):
        Measurement(
            **make_measurement_data(
                positie={"pagina": page, "x": 1.0, "y": 1.0, "eenheid": "pt"}
            )
        )


def test_unknown_direction_is_rejected():
    with pytest.raises(ValidationError):
        Measurement(**make_measurement_data(richting="schuin"))


def test_unknown_source_type_is_rejected():
    with pytest.raises(ValidationError):
        Measurement(
            **make_measurement_data(bron={"type": "ocr", "bestand": "x.pdf"})
        )


@pytest.mark.parametrize("filename", ["", "   "])
def test_empty_source_file_is_rejected(filename):
    with pytest.raises(ValidationError):
        Measurement(
            **make_measurement_data(bron={"type": "vector", "bestand": filename})
        )


@pytest.mark.parametrize("measurement_id", ["", "   "])
def test_empty_id_is_rejected(measurement_id):
    with pytest.raises(ValidationError):
        Measurement(**make_measurement_data(id=measurement_id))


def test_unknown_position_unit_is_rejected():
    with pytest.raises(ValidationError):
        Measurement(
            **make_measurement_data(
                positie={"pagina": 1, "x": 1.0, "y": 1.0, "eenheid": "mm"}
            )
        )


def test_unknown_measurement_unit_is_rejected():
    with pytest.raises(ValidationError):
        Measurement(**make_measurement_data(eenheid="m"))


@pytest.mark.parametrize(
    "overrides",
    [
        {"schaal": 100},
        {"positie": {"pagina": 1, "x": 1.0, "y": 1.0, "eenheid": "pt", "z": 0}},
        {"bron": {"type": "vector", "bestand": "x.pdf", "pagina": 1}},
    ],
)
def test_unknown_extra_field_is_rejected(overrides):
    with pytest.raises(ValidationError):
        Measurement(**make_measurement_data(**overrides))


def test_unknown_extra_field_on_result_is_rejected():
    with pytest.raises(ValidationError):
        ExtractionResult(maten=[], schaal=100)


# ExtractionResult: unieke id's, lege lijst, gereserveerd veld
def test_duplicate_ids_are_rejected():
    with pytest.raises(ValidationError):
        ExtractionResult(
            maten=[make_measurement_data(id="m1"), make_measurement_data(id="m1")]
        )


def test_empty_result_is_valid():
    result = ExtractionResult(maten=[])
    assert result.maten == []
    assert result.formaat_versie == "0.1"


def test_structural_parameters_default_to_null():
    assert ExtractionResult().constructieve_parameters is None


@pytest.mark.parametrize("value", [{}, {"dragende_wanden": []}, [], "x", 0])
def test_structural_parameters_with_value_are_rejected(value):
    with pytest.raises(ValidationError):
        ExtractionResult(maten=[], constructieve_parameters=value)


def test_unknown_format_version_is_rejected():
    with pytest.raises(ValidationError):
        ExtractionResult(formaat_versie="0.2")


# JSON round-trip met de spikewaarden van Naxosdreef plus één onzekere scanmaat.
# Breedte 25370 mm en diepte 9860 mm komen uit de spike. De scanmaat (25400 mm,
# bestand naxosdreef_scan.png) is FICTIEF: van Naxosdreef bestaat in de spike geen
# scan. Alle coördinaten zijn eveneens verzonnen.
def build_naxosdreef_result() -> ExtractionResult:
    return ExtractionResult(
        maten=[
            {
                "id": "breedte",
                "waarde": 25370,
                "positie": {"pagina": 1, "x": 412.3, "y": 88.0, "eenheid": "pt"},
                "richting": "horizontaal",
                "bron": {"type": "vector", "bestand": "naxosdreef.pdf"},
                "betrouwbaarheid": "bewezen",
                "onderbouwing": "som van de deelmaten is gelijk aan de totaalmaat",
                "ruwe_tekst": "25370",
            },
            {
                "id": "diepte",
                "waarde": 9860,
                "positie": {"pagina": 1, "x": 35.0, "y": 300.5, "eenheid": "pt"},
                "richting": "verticaal",
                "bron": {"type": "vector", "bestand": "naxosdreef.pdf"},
                "betrouwbaarheid": "onzeker",
                "ruwe_tekst": "9860",
            },
            {
                "id": "scan-breedte",
                "waarde": 25400,
                "positie": {"pagina": 1, "x": 1820, "y": 240, "eenheid": "px"},
                "richting": "horizontaal",
                "bron": {
                    "type": "scan",
                    "bestand": "naxosdreef_scan.png",
                    "toelichting": "fictieve testwaarde",
                },
                "betrouwbaarheid": "onzeker",
                "ruwe_tekst": "25400",
            },
        ]
    )


def test_json_round_trip_gives_equal_object():
    result = build_naxosdreef_result()
    restored = ExtractionResult.from_json(result.to_json())
    assert restored == result


def test_json_uses_dutch_field_names_and_plain_labels():
    data = json.loads(build_naxosdreef_result().to_json())
    assert set(data) == {"formaat_versie", "maten", "constructieve_parameters"}
    assert data["constructieve_parameters"] is None

    width = data["maten"][0]
    assert set(width) == {
        "id",
        "waarde",
        "eenheid",
        "positie",
        "richting",
        "bron",
        "betrouwbaarheid",
        "onderbouwing",
        "ruwe_tekst",
    }
    assert width["waarde"] == 25370
    assert width["eenheid"] == "mm"
    assert width["richting"] == "horizontaal"
    assert width["betrouwbaarheid"] == "bewezen"
    assert data["maten"][1]["waarde"] == 9860
    assert data["maten"][1]["richting"] == "verticaal"
    assert data["maten"][2]["betrouwbaarheid"] == "onzeker"
    assert data["maten"][2]["bron"]["type"] == "scan"
