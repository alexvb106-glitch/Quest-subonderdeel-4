"""Ingang voor aangeleverde PDF-bestanden (slice S1.2).

Bepaalt van een PDF-bestand op schijf of het een vector-PDF of een scan is en
stuurt het door naar de verwerker van die route. Onbekende of corrupte bestanden
geven een IntakeError met een vaste code en een leesbare Nederlandse boodschap.
Geen tekst- of maatextractie, beeldbewerking of API-koppeling: dat hoort bij
latere slices (S1.3, S1.5) en bij het nog open uploadpad.
"""

from collections import Counter
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Annotated, Literal

import pdfplumber
from pdfminer.pdfdocument import PDFDocument, PDFEncryptionError
from pdfminer.pdfparser import PDFParser, PDFSyntaxError
from pdfminer.pdftypes import PDFObjectNotFound, PDFObjRef
from pdfplumber.utils.exceptions import PdfminerException
from pydantic import BaseModel, ConfigDict, Field

# _STRICT_MODEL wordt overgenomen uit S1.1, zodat beide modellen gegarandeerd dezelfde
# strikte configuratie houden (geen kopie die uit de pas kan gaan lopen)
from onderdeel4.intermediate_format import _STRICT_MODEL, ExtractionResult, NonEmptyText

# Drempels voor de indeling per pagina. VOORLOPIGE waarden: nog niet getoetst op
# echte archief-PDF's. Bijstellen aan de hand van de tellingen per pagina van
# echte testtekeningen (zie plan S1.2, aanname 1 en 8).
# - MIN_VECTOR_OBJECTS: minimaal aantal lijnen + rechthoeken + curves voor een vectorpagina.
MIN_VECTOR_OBJECTS = 50
# - MIN_SCAN_IMAGE_PIXELS: minimale langste zijde (eigen pixelresolutie) van een
#   afbeelding om als scan te tellen; de grootte op het blad telt niet.
MIN_SCAN_IMAGE_PIXELS = 1000

# De PDF-kop moet binnen de eerste 1024 bytes staan; de extensie telt niet
_PDF_HEADER = b"%PDF-"
_HEADER_SEARCH_BYTES = 1024

# Soorten per pagina en routes per bestand. De routes komen overeen met SourceType uit S1.1.
PageKind = Literal["vector", "scan", "leeg"]
Route = Literal["vector", "scan"]

# Verwerker van een route: krijgt het pad en de indeling, levert het tussenformaat (S1.1)
Handler = Callable[[Path, "PdfClassification"], ExtractionResult]

# Niet-negatieve telling
Count = Annotated[int, Field(ge=0)]


# Fout van de ingang: vaste code plus Nederlandse boodschap met alleen de bestandsnaam.
# Bewust los van ApiError (S0.3): de ingang is (nog) niet aan de API gekoppeld.
class IntakeError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


# Uitkomst van de indeling. Zelfde strikte configuratie als het tussenformaat (S1.1):
# onbekende velden geweigerd, ook toewijzingen na constructie gevalideerd.
# Indeling en tellingen van één pagina (1-gebaseerd paginanummer).
# De tellingen blijven bewaard zodat het rapport (S1.6) kan laten zien waarom
# een pagina zo is ingedeeld, en het team de drempels kan toetsen.
class PageClassification(BaseModel):
    model_config = ConfigDict(**_STRICT_MODEL)

    pagina: int = Field(ge=1)
    soort: PageKind
    aantal_tekens: Count
    aantal_vectorobjecten: Count
    grootste_afbeelding_px: Count


# Indeling van het hele bestand: bestandsnaam, gekozen route en de pagina's
class PdfClassification(BaseModel):
    model_config = ConfigDict(**_STRICT_MODEL, str_strip_whitespace=True)

    bestand: NonEmptyText
    route: Route
    paginas: list[PageClassification] = Field(min_length=1)


# Fout bij een leesweigering van het besturingssysteem, zonder systeemdetails in de boodschap
def _not_readable(name: str) -> IntakeError:
    return IntakeError(
        "bestand_niet_leesbaar",
        f"Het bestand '{name}' kan niet worden gelezen. Controleer of het bestand "
        "niet in gebruik is en of er leesrechten op staan.",
    )


# Bestand controleren vóór het openen: bestaat het, is het niet leeg, en is het een PDF
def _check_file(path: Path) -> None:
    name = path.name
    if not path.is_file():
        raise IntakeError("bestand_niet_gevonden", f"Het bestand '{name}' is niet gevonden.")
    # Leesfouten van het besturingssysteem (bijv. geen leesrechten, bestand vergrendeld)
    # als nette fout melden, zonder systeemdetails in de boodschap
    try:
        size = path.stat().st_size
        if size > 0:
            with path.open("rb") as file:
                start = file.read(_HEADER_SEARCH_BYTES)
    except OSError as exc:
        raise _not_readable(name) from exc
    if size == 0:
        raise IntakeError("bestand_leeg", f"Het bestand '{name}' is leeg (0 bytes).")
    if _PDF_HEADER not in start:
        raise IntakeError(
            "geen_pdf",
            f"Het bestand '{name}' is geen PDF. Lever een PDF-bestand aan.",
        )


# Grootste afbeelding op een pagina: hoogste langste zijde uit de eigen pixelresolutie
# (srcsize). Plaatsing en getekende grootte op het blad tellen niet mee.
# Een ontbrekende of onleesbare resolutie telt als 0 (geen bruikbare afbeelding).
def _largest_image_px(images: list[dict]) -> int:
    largest = 0
    for image in images:
        try:
            width, height = (int(value) for value in image["srcsize"])
        except (KeyError, TypeError, ValueError):
            continue
        largest = max(largest, width, height)
    return largest


# Indeling van één pagina, in vaste volgorde (zie plan S1.2, §3.3b):
# 1. genoeg vectorobjecten -> vector; 2. afbeelding met hoge resolutie -> scan;
# 3. tekens -> vector; 4. anders leeg.
def _classify_counts(vector_objects: int, chars: int, largest_image_px: int) -> PageKind:
    if vector_objects >= MIN_VECTOR_OBJECTS:
        return "vector"
    if largest_image_px >= MIN_SCAN_IMAGE_PIXELS:
        return "scan"
    if chars > 0:
        return "vector"
    return "leeg"


# Tellen per pagina met pdfplumber, en indelen
def _classify_page(page) -> PageClassification:
    vector_objects = len(page.lines) + len(page.rects) + len(page.curves)
    chars = len(page.chars)
    largest_image_px = _largest_image_px(page.images)
    return PageClassification(
        pagina=page.page_number,
        soort=_classify_counts(vector_objects, chars, largest_image_px),
        aantal_tekens=chars,
        aantal_vectorobjecten=vector_objects,
        grootste_afbeelding_px=largest_image_px,
    )


# Kringverwijzing tussen PDF-objecten (bijv. "2 0 obj 2 0 R endobj"). pdfminer volgt
# zo'n keten in een while-lus zonder einde, waardoor een bestand van een paar honderd
# bytes het proces voor altijd laat draaien (gevonden bij de breektest van S1.2).
class _ReferenceCycleError(PDFSyntaxError):
    pass


# PDFDocument die bij elk opgehaald object de keten van verwijzingen naloopt en bij een
# kring een fout geeft in plaats van eindeloos te blijven zoeken. Alleen voor de controle
# vooraf; pdfplumber zelf blijft het gewone PDFDocument gebruiken.
class _CycleCheckingDocument(PDFDocument):
    def getobj(self, objid: int) -> object:
        obj = super().getobj(objid)
        seen = {objid}
        target = obj
        while isinstance(target, PDFObjRef):
            if target.objid in seen:
                raise _ReferenceCycleError(f"kringverwijzing bij object {objid}")
            seen.add(target.objid)
            try:
                target = super().getobj(target.objid)
            except PDFObjectNotFound:
                break
        return obj


# Controle vooraf op kringverwijzingen: eerst de trailer (Root, Info, Encrypt, bij het
# openen), daarna elk object uit de xref. Andere fouten bij losse objecten worden hier
# genegeerd: die behandelt pdfplumber zelf, zodat deze controle geen bestanden weigert
# die pdfplumber wel kan lezen.
def _check_reference_cycles(path: Path) -> None:
    with path.open("rb") as file:
        document = _CycleCheckingDocument(PDFParser(file))
        for xref in document.xrefs:
            for objid in xref.get_objids():
                try:
                    document.getobj(objid)
                except _ReferenceCycleError:
                    raise
                except Exception:
                    continue


# PDF openen en alle pagina's indelen. Fouten van pdfplumber/pdfminer worden vertaald
# naar een IntakeError; de oorspronkelijke fout blijft als oorzaak bewaard (raise ... from),
# maar de interne details komen niet in de boodschap.
def _classify_pages(path: Path) -> list[PageClassification]:
    name = path.name
    try:
        _check_reference_cycles(path)
        with pdfplumber.open(path) as pdf:
            pages = []
            for page in pdf.pages:
                pages.append(_classify_page(page))
                # Tussenresultaten van de pagina vrijgeven, zodat het geheugen bij
                # veel pagina's niet blijft oplopen
                page.close()
            return pages
    except Exception as exc:
        cause = exc.args[0] if isinstance(exc, PdfminerException) and exc.args else exc
        # Bestand verdwenen of vergrendeld tussen de controle vooraf en het openen
        if isinstance(cause, FileNotFoundError):
            raise IntakeError(
                "bestand_niet_gevonden", f"Het bestand '{name}' is niet gevonden."
            ) from exc
        if isinstance(cause, OSError):
            raise _not_readable(name) from exc
        if isinstance(cause, PDFEncryptionError):
            raise IntakeError(
                "pdf_versleuteld",
                f"Het bestand '{name}' is beveiligd met een wachtwoord en kan niet "
                "worden gelezen. Lever een onbeveiligde versie aan.",
            ) from exc
        raise IntakeError(
            "pdf_beschadigd",
            f"Het bestand '{name}' is beschadigd of kan niet als PDF worden gelezen.",
        ) from exc


# Paginanummers als leesbare opsomming, bijv. "1, 3"
def _page_list(pages: list[PageClassification], kind: PageKind) -> str:
    return ", ".join(str(page.pagina) for page in pages if page.soort == kind)


# Indeling van het bestand: lege pagina's tellen niet mee; één soort -> die route;
# beide soorten -> pdf_gemengd; alleen leeg -> pdf_zonder_inhoud
def _choose_route(name: str, pages: list[PageClassification]) -> Route:
    kinds = Counter(page.soort for page in pages)
    if kinds["vector"] and kinds["scan"]:
        raise IntakeError(
            "pdf_gemengd",
            f"Het bestand '{name}' bevat zowel vectorpagina's (pagina "
            f"{_page_list(pages, 'vector')}) als scanpagina's (pagina "
            f"{_page_list(pages, 'scan')}). Splits het bestand en lever de "
            "vector- en scanpagina's apart aan.",
        )
    if kinds["vector"]:
        return "vector"
    if kinds["scan"]:
        return "scan"
    raise IntakeError(
        "pdf_zonder_inhoud",
        f"Het bestand '{name}' bevat alleen lege pagina's.",
    )


def classify_pdf(path: str | Path) -> PdfClassification:
    """Bepaal of een PDF-bestand een vector-PDF of een scan is.

    Geeft per pagina de soort en de tellingen terug, plus de route van het hele
    bestand. Gooit een IntakeError bij een ontbrekend, leeg, onbekend, corrupt,
    versleuteld of gemengd bestand, en bij een PDF zonder pagina's of inhoud.
    """
    file_path = Path(path)
    _check_file(file_path)
    pages = _classify_pages(file_path)
    if not pages:
        raise IntakeError(
            "pdf_zonder_paginas",
            f"Het bestand '{file_path.name}' bevat geen pagina's.",
        )
    route = _choose_route(file_path.name, pages)
    return PdfClassification(bestand=file_path.name, route=route, paginas=pages)


def route_pdf(path: str | Path, handlers: Mapping[str, Handler]) -> ExtractionResult:
    """Deel een PDF-bestand in en stuur het door naar de verwerker van die route.

    handlers koppelt "vector" en/of "scan" aan een verwerker. Er is bewust geen
    ingebouwd register: de routes (S1.3, S1.5) leveren hun eigen verwerker aan.
    """
    file_path = Path(path)
    classification = classify_pdf(file_path)

    # Verwerker kiezen; ontbreekt die, dan is de route (nog) niet beschikbaar
    handler = handlers.get(classification.route)
    if handler is None:
        raise IntakeError(
            "route_niet_beschikbaar",
            f"Het bestand '{file_path.name}' is ingedeeld als {classification.route}, "
            f"maar de {classification.route}route is (nog) niet beschikbaar.",
        )

    # Alleen het type van de uitkomst controleren; een verkeerd type is een programmeerfout
    result = handler(file_path, classification)
    if not isinstance(result, ExtractionResult):
        raise TypeError(
            f"verwerker voor route '{classification.route}' gaf {type(result).__name__} "
            "terug in plaats van ExtractionResult"
        )
    return result
