import os
import subprocess
import sys
from pathlib import Path

import pdfplumber
import pytest
from pydantic import ValidationError

import onderdeel4.intake as intake
from onderdeel4.intake import (
    MIN_SCAN_IMAGE_PIXELS,
    MIN_VECTOR_OBJECTS,
    IntakeError,
    PageClassification,
    PdfClassification,
    classify_pdf,
    route_pdf,
)
from onderdeel4.intermediate_format import ExtractionResult, Measurement
from pdf_fixtures import A0, ImageSpec, PageSpec, write_pdf, write_raw_pdf

# Alle bestandsnamen en teksten in dit bestand zijn fictief; de PDF's worden per
# test in tmp_path gegenereerd (geen echte bouwtekeningen in de repo).

# Afbeeldingsresoluties, afgeleid van de drempel zodat de tests blijven kloppen
# als MIN_SCAN_IMAGE_PIXELS later wordt bijgesteld.
HIGH_RES = (MIN_SCAN_IMAGE_PIXELS + 200, MIN_SCAN_IMAGE_PIXELS - 200)  # bijv. 1200 x 800
LOGO_RES = (MIN_SCAN_IMAGE_PIXELS // 10, MIN_SCAN_IMAGE_PIXELS // 20)  # bijv. 100 x 50
TEXT = "Doorsnede A-A"


# Hulpfuncties voor afbeeldingen: paginavullend, of klein geplaatst op het blad
def full_page_image(resolution: tuple[int, int]) -> ImageSpec:
    return ImageSpec(*resolution)


def small_placed_image(resolution: tuple[int, int]) -> ImageSpec:
    return ImageSpec(*resolution, x=100, y=100, draw_width=120, draw_height=80)


# Hulpfunctie: één PDF met de opgegeven pagina's in tmp_path
def make_pdf(tmp_path: Path, *pages: PageSpec, name: str = "tekening.pdf", **options) -> Path:
    return write_pdf(tmp_path / name, list(pages), **options)


# Inhoud per pagina zoals pdfplumber die ziet, los van intake.py:
# (lijnen + rechthoeken + curves, aantal tekens, srcsize van elke afbeelding)
def read_page_contents(path: Path, password: str | None = None) -> list[tuple]:
    with pdfplumber.open(path, password=password) as pdf:
        return [
            (
                len(page.lines) + len(page.rects) + len(page.curves),
                len(page.chars),
                [tuple(image["srcsize"]) for image in page.images],
            )
            for page in pdf.pages
        ]


# Soorten pagina's: (fixture, verwachte soort, verwachte inhoud volgens pdfplumber).
# De verwachte inhoud wordt eerst los gecontroleerd (tegen een controle die niets
# controleert, Spike_overdracht.md bevinding 5), daarna wordt de indeling getest.
PAGE_CASES = {
    # Indeling per pagina
    "alleen_tekst": (PageSpec(text=TEXT), "vector", (0, len(TEXT), [])),
    "alleen_lijnen_op_drempel": (
        PageSpec(lines=MIN_VECTOR_OBJECTS),
        "vector",
        (MIN_VECTOR_OBJECTS, 0, []),
    ),
    "lijnen_en_rechthoeken_op_drempel": (
        PageSpec(lines=MIN_VECTOR_OBJECTS - 10, rects=10),
        "vector",
        (MIN_VECTOR_OBJECTS, 0, []),
    ),
    # Curves tellen mee als vectorobject (lijnen + rechthoeken + curves)
    "lijnen_rechthoeken_en_curves_op_drempel": (
        PageSpec(lines=MIN_VECTOR_OBJECTS - 20, rects=10, curves=10),
        "vector",
        (MIN_VECTOR_OBJECTS, 0, []),
    ),
    "alleen_curves_net_onder_drempel": (
        PageSpec(curves=MIN_VECTOR_OBJECTS - 1),
        "leeg",
        (MIN_VECTOR_OBJECTS - 1, 0, []),
    ),
    "scan_paginavullend": (
        PageSpec(images=[full_page_image(HIGH_RES)]),
        "scan",
        (0, 0, [HIGH_RES]),
    ),
    "scan_klein_op_a0": (
        PageSpec(size=A0, images=[small_placed_image(HIGH_RES)]),
        "scan",
        (0, 0, [HIGH_RES]),
    ),
    "scan_met_ocr_laag": (
        PageSpec(text=TEXT, invisible_text=True, images=[full_page_image(HIGH_RES)]),
        "scan",
        (0, len(TEXT), [HIGH_RES]),
    ),
    "vector_met_grote_afbeelding": (
        PageSpec(lines=MIN_VECTOR_OBJECTS, text=TEXT, images=[full_page_image(HIGH_RES)]),
        "vector",
        (MIN_VECTOR_OBJECTS, len(TEXT), [HIGH_RES]),
    ),
    "vector_met_klein_logo": (
        PageSpec(lines=MIN_VECTOR_OBJECTS, images=[small_placed_image(LOGO_RES)]),
        "vector",
        (MIN_VECTOR_OBJECTS, 0, [LOGO_RES]),
    ),
    "alleen_klein_logo": (
        PageSpec(images=[small_placed_image(LOGO_RES)]),
        "leeg",
        (0, 0, [LOGO_RES]),
    ),
    "lege_pagina": (PageSpec(), "leeg", (0, 0, [])),
    "scan_met_kader": (
        PageSpec(lines=4, images=[full_page_image(HIGH_RES)]),
        "scan",
        (4, 0, [HIGH_RES]),
    ),
    # Grenswaarden vectorobjecten, zonder en met afbeelding met hoge resolutie
    "lijnen_net_onder_drempel": (
        PageSpec(lines=MIN_VECTOR_OBJECTS - 1),
        "leeg",
        (MIN_VECTOR_OBJECTS - 1, 0, []),
    ),
    "lijnen_net_onder_drempel_met_scan": (
        PageSpec(lines=MIN_VECTOR_OBJECTS - 1, images=[full_page_image(HIGH_RES)]),
        "scan",
        (MIN_VECTOR_OBJECTS - 1, 0, [HIGH_RES]),
    ),
    "lijnen_op_drempel_met_scan": (
        PageSpec(lines=MIN_VECTOR_OBJECTS, images=[full_page_image(HIGH_RES)]),
        "vector",
        (MIN_VECTOR_OBJECTS, 0, [HIGH_RES]),
    ),
    # Grenswaarden pixelresolutie; de langste zijde telt
    "afbeelding_net_onder_drempel": (
        PageSpec(images=[full_page_image((MIN_SCAN_IMAGE_PIXELS - 1, 500))]),
        "leeg",
        (0, 0, [(MIN_SCAN_IMAGE_PIXELS - 1, 500)]),
    ),
    "afbeelding_op_drempel": (
        PageSpec(images=[full_page_image((MIN_SCAN_IMAGE_PIXELS, 500))]),
        "scan",
        (0, 0, [(MIN_SCAN_IMAGE_PIXELS, 500)]),
    ),
    "staande_afbeelding": (
        PageSpec(images=[full_page_image((400, MIN_SCAN_IMAGE_PIXELS))]),
        "scan",
        (0, 0, [(400, MIN_SCAN_IMAGE_PIXELS)]),
    ),
    # Meerdere afbeeldingen: de grootste telt
    "logo_en_scan": (
        PageSpec(images=[small_placed_image(LOGO_RES), full_page_image(HIGH_RES)]),
        "scan",
        (0, 0, [LOGO_RES, HIGH_RES]),
    ),
}


# Fixtures controleren met pdfplumber zelf: de bedoelde inhoud zit er echt in
@pytest.mark.parametrize("case", PAGE_CASES)
def test_fixture_contains_intended_content(tmp_path, case):
    page, _, expected_content = PAGE_CASES[case]
    assert read_page_contents(make_pdf(tmp_path, page)) == [expected_content]


# Indeling per pagina volgens het criterium (soort inhoud, niet beelddekking)
def classify_single_page(tmp_path: Path, page: PageSpec, expected_kind: str):
    # Een bestand met alleen een lege pagina wordt geweigerd (pdf_zonder_inhoud);
    # daarom krijgt een lege pagina een tekstpagina erachter, zodat het bestand een
    # route heeft. Bekeken wordt steeds alleen de eerste pagina.
    extra = [PageSpec(text=TEXT)] if expected_kind == "leeg" else []
    return classify_pdf(make_pdf(tmp_path, page, *extra)).paginas[0]


@pytest.mark.parametrize("case", PAGE_CASES)
def test_page_is_classified_by_content_type(tmp_path, case):
    page, expected_kind, _ = PAGE_CASES[case]
    assert classify_single_page(tmp_path, page, expected_kind).soort == expected_kind


# Tellingen in het model komen overeen met de inhoud van de fixture
@pytest.mark.parametrize("case", PAGE_CASES)
def test_page_counts_match_fixture(tmp_path, case):
    page, expected_kind, (vector_objects, chars, image_sizes) = PAGE_CASES[case]
    result = classify_single_page(tmp_path, page, expected_kind)
    assert result.pagina == 1
    assert result.aantal_vectorobjecten == vector_objects
    assert result.aantal_tekens == chars
    assert result.grootste_afbeelding_px == max((max(size) for size in image_sizes), default=0)


# Vaste pagina's voor de tests op bestandsniveau
VECTOR_PAGE = PageSpec(lines=MIN_VECTOR_OBJECTS, text=TEXT)
SCAN_PAGE = PageSpec(images=[full_page_image(HIGH_RES)])
EMPTY_PAGE = PageSpec()


# Fixtures op bestandsniveau controleren: de pagina's zijn wat ze moeten zijn
def test_file_level_fixture_pages_contain_intended_content(tmp_path):
    path = make_pdf(tmp_path, VECTOR_PAGE, SCAN_PAGE, EMPTY_PAGE)
    assert read_page_contents(path) == [
        (MIN_VECTOR_OBJECTS, len(TEXT), []),
        (0, 0, [HIGH_RES]),
        (0, 0, []),
    ]


# Indeling van het hele bestand
def test_multiple_vector_pages_give_vector_route(tmp_path):
    result = classify_pdf(make_pdf(tmp_path, VECTOR_PAGE, PageSpec(text=TEXT), VECTOR_PAGE))
    assert result.route == "vector"
    assert [page.pagina for page in result.paginas] == [1, 2, 3]
    assert [page.soort for page in result.paginas] == ["vector", "vector", "vector"]


def test_multiple_scan_pages_give_scan_route(tmp_path):
    result = classify_pdf(make_pdf(tmp_path, SCAN_PAGE, SCAN_PAGE))
    assert result.route == "scan"


def test_vector_with_empty_page_gives_vector_route(tmp_path):
    result = classify_pdf(make_pdf(tmp_path, EMPTY_PAGE, VECTOR_PAGE, EMPTY_PAGE))
    assert result.route == "vector"
    assert [page.soort for page in result.paginas] == ["leeg", "vector", "leeg"]


def test_scan_with_empty_page_gives_scan_route(tmp_path):
    result = classify_pdf(make_pdf(tmp_path, SCAN_PAGE, EMPTY_PAGE))
    assert result.route == "scan"
    assert [page.soort for page in result.paginas] == ["scan", "leeg"]


def test_result_contains_file_name_only(tmp_path):
    result = classify_pdf(make_pdf(tmp_path, VECTOR_PAGE, name="naxos_test.pdf"))
    assert result.bestand == "naxos_test.pdf"


def test_path_as_string_is_accepted(tmp_path):
    result = classify_pdf(str(make_pdf(tmp_path, VECTOR_PAGE)))
    assert result.route == "vector"


def test_mixed_file_is_refused_with_page_numbers(tmp_path):
    path = make_pdf(tmp_path, VECTOR_PAGE, SCAN_PAGE, EMPTY_PAGE, VECTOR_PAGE, SCAN_PAGE)
    with pytest.raises(IntakeError) as caught:
        classify_pdf(path)
    assert caught.value.code == "pdf_gemengd"
    assert "vectorpagina's (pagina 1, 4)" in caught.value.message
    assert "scanpagina's (pagina 2, 5)" in caught.value.message


def test_only_empty_pages_is_refused(tmp_path):
    path = make_pdf(tmp_path, EMPTY_PAGE, PageSpec(images=[small_placed_image(LOGO_RES)]))
    with pytest.raises(IntakeError) as caught:
        classify_pdf(path)
    assert caught.value.code == "pdf_zonder_inhoud"


# Herkenning op inhoud (PDF-kop), niet op extensie
def test_pdf_with_other_extension_is_read(tmp_path):
    result = classify_pdf(make_pdf(tmp_path, VECTOR_PAGE, name="tekening.bin"))
    assert result.route == "vector"


def test_pdf_header_after_leading_bytes_is_accepted(tmp_path):
    source = make_pdf(tmp_path, VECTOR_PAGE)
    path = tmp_path / "met_voorloop.pdf"
    path.write_bytes(b"x" * 100 + source.read_bytes())
    assert classify_pdf(path).route == "vector"


# Fouten: elk een IntakeError met de juiste code, een Nederlandse boodschap met
# alleen de bestandsnaam, en geen volledig pad of pdfminer-details in de boodschap
def assert_intake_error(path: Path, code: str) -> IntakeError:
    with pytest.raises(IntakeError) as caught:
        classify_pdf(path)
    error = caught.value
    assert error.code == code
    assert error.message and str(error) == error.message
    assert path.name in error.message
    assert str(path.parent) not in error.message
    assert "Het bestand" in error.message
    for internal in ("Traceback", "pdfminer", "PSEOF", "PDFSyntaxError", "Error("):
        assert internal not in error.message
    return error


def test_missing_file_gives_not_found(tmp_path):
    assert_intake_error(tmp_path / "bestaat_niet.pdf", "bestand_niet_gevonden")


def test_directory_gives_not_found(tmp_path):
    directory = tmp_path / "map.pdf"
    directory.mkdir()
    assert_intake_error(directory, "bestand_niet_gevonden")


def test_zero_byte_file_gives_empty_file(tmp_path):
    path = tmp_path / "leeg.pdf"
    path.write_bytes(b"")
    assert_intake_error(path, "bestand_leeg")


# Leesrechten zijn op Windows niet betrouwbaar af te nemen; daarom wordt de leesfout
# van het besturingssysteem nagebootst bij het openen van het bestand
def test_unreadable_file_gives_not_readable(tmp_path, monkeypatch):
    path = write_pdf(tmp_path / "vergrendeld.pdf", [VECTOR_PAGE])

    def deny_open(self, *args, **kwargs):
        raise PermissionError(13, "Permission denied", str(self))

    monkeypatch.setattr(Path, "open", deny_open)
    error = assert_intake_error(path, "bestand_niet_leesbaar")
    assert "Permission denied" not in error.message
    assert isinstance(error.__cause__, PermissionError)


def test_text_file_with_pdf_extension_gives_not_a_pdf(tmp_path):
    path = tmp_path / "tekening.pdf"
    path.write_text("Dit is geen PDF maar een tekstbestand.", encoding="utf-8")
    assert_intake_error(path, "geen_pdf")


def test_png_file_gives_not_a_pdf(tmp_path):
    path = tmp_path / "plattegrond.png"
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
    assert_intake_error(path, "geen_pdf")


def test_pdf_header_beyond_search_window_gives_not_a_pdf(tmp_path):
    source = make_pdf(tmp_path, VECTOR_PAGE)
    path = tmp_path / "kop_te_laat.pdf"
    path.write_bytes(b"x" * 1024 + source.read_bytes())
    assert_intake_error(path, "geen_pdf")


def test_truncated_pdf_gives_damaged(tmp_path):
    source = make_pdf(tmp_path, VECTOR_PAGE)
    path = tmp_path / "afgekapt.pdf"
    path.write_bytes(source.read_bytes()[:300])
    error = assert_intake_error(path, "pdf_beschadigd")
    assert error.__cause__ is not None


def test_garbage_after_pdf_header_gives_damaged(tmp_path):
    path = tmp_path / "onzin.pdf"
    path.write_bytes(b"%PDF-1.4\nonzin onzin onzin\n")
    error = assert_intake_error(path, "pdf_beschadigd")
    assert error.__cause__ is not None


def test_encrypted_fixture_is_really_encrypted(tmp_path):
    path = make_pdf(tmp_path, VECTOR_PAGE, user_password="geheim")
    # Met het wachtwoord leesbaar en met de bedoelde inhoud; zonder wachtwoord niet
    assert read_page_contents(path, password="geheim") == [(MIN_VECTOR_OBJECTS, len(TEXT), [])]
    with pytest.raises(Exception):
        read_page_contents(path)


def test_encrypted_pdf_gives_encrypted(tmp_path):
    path = make_pdf(tmp_path, VECTOR_PAGE, user_password="geheim")
    assert_intake_error(path, "pdf_versleuteld")


def test_pdf_without_pages_gives_no_pages(tmp_path):
    path = make_pdf(tmp_path)
    assert read_page_contents(path) == []
    assert_intake_error(path, "pdf_zonder_paginas")


# Breektest: objecten die (via een keten) naar zichzelf verwijzen. pdfminer liep daarop
# vast in een eindeloze lus (een bestand van een paar honderd bytes hield het proces
# voor altijd bezig).
_CATALOG = b"<< /Type /Catalog /Pages 2 0 R >>"
_PAGES = b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>"
_PAGE = b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R >>"
_CONTENT = b"<< /Length 13 >>\nstream\n0 0 m 9 9 l S\nendstream"

CYCLE_CASES = {
    "root_naar_zichzelf": [b"1 0 R"],
    "root_via_keten": [b"2 0 R", b"1 0 R"],
    "pages_naar_zichzelf": [_CATALOG, b"2 0 R"],
    "contents_naar_zichzelf": [_CATALOG, _PAGES, _PAGE.replace(b"4 0 R", b"5 0 R"), _CONTENT, b"5 0 R"],
    "mediabox_naar_zichzelf": [_CATALOG, _PAGES, _PAGE.replace(b"[0 0 595 842]", b"5 0 R"), _CONTENT, b"5 0 R"],
}


# Indeling in een apart proces met een ruime tijdslimiet: een terugval naar de eindeloze
# lus laat de test dan falen in plaats van de hele testsuite te laten hangen.
_CLASSIFY_SCRIPT = (
    "import sys\n"
    "from onderdeel4.intake import IntakeError, classify_pdf\n"
    "try:\n"
    "    classify_pdf(sys.argv[1])\n"
    "    print('geen_fout')\n"
    "except IntakeError as error:\n"
    "    print(error.code)\n"
)


def classify_code_in_subprocess(path: Path, seconds: float = 60.0) -> str:
    source_dir = Path(__file__).resolve().parents[1] / "src"
    environment = {**os.environ, "PYTHONPATH": str(source_dir)}
    try:
        completed = subprocess.run(
            [sys.executable, "-c", _CLASSIFY_SCRIPT, str(path)],
            capture_output=True,
            text=True,
            timeout=seconds,
            env=environment,
        )
    except subprocess.TimeoutExpired:
        pytest.fail("classify_pdf blijft hangen op een kringverwijzing")
    return completed.stdout.strip() or completed.stderr.strip().splitlines()[-1]


@pytest.mark.parametrize("objects", CYCLE_CASES.values(), ids=CYCLE_CASES.keys())
def test_reference_cycle_gives_damaged_instead_of_hanging(tmp_path, objects):
    path = write_raw_pdf(tmp_path / "kring.pdf", objects)
    assert classify_code_in_subprocess(path) == "pdf_beschadigd"
    # Pas nu het proces gegarandeerd stopt, ook de boodschap in dit proces controleren
    error = assert_intake_error(path, "pdf_beschadigd")
    assert "kringverwijzing" not in error.message


# Controle dat de raw-schrijver zelf een leesbare PDF maakt (zonder kring), zodat de
# kringtests niet slagen op een bestand dat om een andere reden kapot is
def test_raw_fixture_without_cycle_is_readable(tmp_path):
    path = write_raw_pdf(tmp_path / "geen_kring.pdf", [_CATALOG, _PAGES, _PAGE, _CONTENT])
    assert read_page_contents(path) == [(1, 0, [])]
    # Eén lijn is te weinig voor vector: leesbaar, maar zonder inhoud (niet beschadigd)
    assert_intake_error(path, "pdf_zonder_inhoud")


# Breektest: het bestand verdwijnt of wordt vergrendeld tussen de controle vooraf en
# het openen door pdfminer. Dat is geen beschadigd bestand.
def test_file_vanishing_after_check_gives_not_found(tmp_path, monkeypatch):
    path = write_pdf(tmp_path / "verdwijnt.pdf", [VECTOR_PAGE])
    original_check = intake._check_file

    def check_then_delete(file_path):
        original_check(file_path)
        file_path.unlink()

    monkeypatch.setattr(intake, "_check_file", check_then_delete)
    error = assert_intake_error(path, "bestand_niet_gevonden")
    assert isinstance(error.__cause__, FileNotFoundError)


def test_file_locked_after_check_gives_not_readable(tmp_path, monkeypatch):
    path = write_pdf(tmp_path / "vergrendeld_later.pdf", [VECTOR_PAGE])
    original_check = intake._check_file

    def check_then_lock(file_path):
        original_check(file_path)

        def deny_open(self, *args, **kwargs):
            raise PermissionError(13, "Permission denied", str(self))

        monkeypatch.setattr(Path, "open", deny_open)

    monkeypatch.setattr(intake, "_check_file", check_then_lock)
    error = assert_intake_error(path, "bestand_niet_leesbaar")
    assert "Permission denied" not in error.message


# Breektest: bij veel pagina's liep het geheugen op omdat pdfplumber de objecten van
# elke pagina bewaart. Elke pagina wordt na het indelen gesloten.
def test_each_page_is_closed_after_classification(tmp_path, monkeypatch):
    path = make_pdf(tmp_path, VECTOR_PAGE, VECTOR_PAGE, VECTOR_PAGE)
    events: list[tuple[str, int]] = []
    original_close = pdfplumber.page.Page.close
    original_classify = intake._classify_page

    def recording_close(self):
        events.append(("sluiten", self.page_number))
        original_close(self)

    def recording_classify(page):
        events.append(("indelen", page.page_number))
        return original_classify(page)

    monkeypatch.setattr(pdfplumber.page.Page, "close", recording_close)
    monkeypatch.setattr(intake, "_classify_page", recording_classify)
    classify_pdf(path)
    # Elke pagina wordt direct na het indelen gesloten, niet pas aan het eind
    assert events[:6] == [
        ("indelen", 1), ("sluiten", 1),
        ("indelen", 2), ("sluiten", 2),
        ("indelen", 3), ("sluiten", 3),
    ]


# Doorsturen naar de juiste verwerker, met stubs die vastleggen of ze zijn aangeroepen
class RecordingHandler:
    def __init__(self, source_type: str):
        self.calls: list[tuple[Path, PdfClassification]] = []
        self.result = ExtractionResult(
            maten=[
                Measurement(
                    id="m1",
                    waarde=1000.0,
                    bron={"type": source_type, "bestand": "tekening.pdf"},
                    betrouwbaarheid="onzeker",
                )
            ]
        )

    def __call__(self, path: Path, classification: PdfClassification) -> ExtractionResult:
        self.calls.append((path, classification))
        return self.result


@pytest.fixture
def handlers():
    return {"vector": RecordingHandler("vector"), "scan": RecordingHandler("scan")}


def test_vector_pdf_goes_to_vector_handler(tmp_path, handlers):
    path = make_pdf(tmp_path, VECTOR_PAGE)
    result = route_pdf(path, handlers)
    assert result is handlers["vector"].result
    assert handlers["scan"].calls == []
    [(called_path, classification)] = handlers["vector"].calls
    assert called_path == path
    assert classification.route == "vector"
    assert classification == classify_pdf(path)


def test_scan_pdf_goes_to_scan_handler(tmp_path, handlers):
    path = make_pdf(tmp_path, SCAN_PAGE)
    result = route_pdf(str(path), handlers)
    assert result is handlers["scan"].result
    assert handlers["vector"].calls == []
    [(called_path, classification)] = handlers["scan"].calls
    assert called_path == path
    assert classification.route == "scan"


def test_missing_handler_gives_route_not_available(tmp_path, handlers):
    path = make_pdf(tmp_path, SCAN_PAGE)
    with pytest.raises(IntakeError) as caught:
        route_pdf(path, {"vector": handlers["vector"]})
    assert caught.value.code == "route_niet_beschikbaar"
    assert "scan" in caught.value.message
    assert handlers["vector"].calls == []


# Bestanden die geweigerd worden voordat er een verwerker aan bod komt
def write_mixed_pdf(tmp_path: Path) -> Path:
    return make_pdf(tmp_path, VECTOR_PAGE, SCAN_PAGE)


def write_corrupt_pdf(tmp_path: Path) -> Path:
    path = tmp_path / "onzin.pdf"
    path.write_bytes(b"%PDF-1.4\nonzin\n")
    return path


@pytest.mark.parametrize("write_file", [write_mixed_pdf, write_corrupt_pdf], ids=["gemengd", "corrupt"])
def test_mixed_or_corrupt_pdf_calls_no_handler(tmp_path, handlers, write_file):
    with pytest.raises(IntakeError):
        route_pdf(write_file(tmp_path), handlers)
    assert handlers["vector"].calls == []
    assert handlers["scan"].calls == []


# Een verwerker die geen ExtractionResult teruggeeft is een programmeerfout (TypeError)
def test_handler_with_wrong_return_type_gives_type_error(tmp_path):
    path = make_pdf(tmp_path, VECTOR_PAGE)
    with pytest.raises(TypeError):
        route_pdf(path, {"vector": lambda path, classification: {"maten": []}})


# Modellen: strikt, met precies de afgesproken velden
VALID_PAGE = {
    "pagina": 1,
    "soort": "vector",
    "aantal_tekens": 12,
    "aantal_vectorobjecten": 50,
    "grootste_afbeelding_px": 0,
}


def test_models_have_exactly_the_agreed_fields():
    assert set(PageClassification.model_fields) == set(VALID_PAGE)
    assert set(PdfClassification.model_fields) == {"bestand", "route", "paginas"}


def test_valid_classification_is_accepted():
    result = PdfClassification(bestand="tekening.pdf", route="vector", paginas=[VALID_PAGE])
    assert result.paginas[0] == PageClassification(**VALID_PAGE)


@pytest.mark.parametrize(
    "overrides",
    [
        {"extra_veld": 1},
        {"route": "leeg"},
        {"route": "handmatig"},
        {"paginas": []},
        {"bestand": "   "},
    ],
    ids=["onbekend_veld", "route_leeg", "route_handmatig", "geen_paginas", "lege_bestandsnaam"],
)
def test_invalid_pdf_classification_is_refused(overrides):
    data = {"bestand": "tekening.pdf", "route": "vector", "paginas": [VALID_PAGE]}
    data.update(overrides)
    with pytest.raises(ValidationError):
        PdfClassification(**data)


@pytest.mark.parametrize(
    "overrides",
    [
        {"aantal_tekens": -1},
        {"aantal_vectorobjecten": -1},
        {"grootste_afbeelding_px": -1},
        {"pagina": 0},
        {"soort": "gemengd"},
        {"beelddekking": 0.5},
    ],
    ids=[
        "negatieve_tekens",
        "negatieve_vectorobjecten",
        "negatieve_afbeelding",
        "pagina_nul",
        "onbekende_soort",
        "beelddekking",
    ],
)
def test_invalid_page_classification_is_refused(overrides):
    with pytest.raises(ValidationError):
        PageClassification(**{**VALID_PAGE, **overrides})
