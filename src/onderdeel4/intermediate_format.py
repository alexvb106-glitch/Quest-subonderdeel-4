"""Tussenformaat voor uitgelezen maten (slice S1.1).

Beide routes (vector-PDF en scan) schrijven naar dit formaat; de controle (S1.4)
en de uitvoer (S1.6) lezen eruit. Dit bestand bevat alleen de datastructuur en
consistentiebewaking, geen detectie, controle of uitvoer.
"""

import unicodedata
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

# Huidige versie van het tussenformaat, zodat latere uitbreidingen herkenbaar zijn
FORMAT_VERSION = "0.1"

# Toegestane waarden: betrouwbaarheidslabels, richting, brontype en positie-eenheid.
# Als Literal, zodat de JSON de kale (Nederlandse) string bevat.
ReliabilityLabel = Literal["bewezen", "onzeker", "ontbreekt"]
Direction = Literal["horizontaal", "verticaal"]
SourceType = Literal["vector", "scan", "handmatig"]
PositionUnit = Literal["pt", "px"]

# Eindig getal: NaN en (-)oneindig worden geweigerd
FiniteFloat = Annotated[float, Field(allow_inf_nan=False)]

# Onzichtbare tekens: witruimte, stuurtekens (Cc), opmaaktekens zoals zero-width space (Cf)
# en scheidingstekens (Z*). Tekst die alleen hieruit bestaat, telt als leeg.
_INVISIBLE_CATEGORIES = {"Cc", "Cf", "Zs", "Zl", "Zp"}


def _has_visible_text(value: str | None) -> bool:
    return bool(value) and any(
        unicodedata.category(char) not in _INVISIBLE_CATEGORIES for char in value
    )


def _require_visible_text(value: str) -> str:
    if not _has_visible_text(value):
        raise ValueError("tekst mag niet leeg zijn of alleen uit onzichtbare tekens bestaan")
    return value


# Niet-lege tekst. Witruimte aan de randen wordt eerst weggehaald via
# str_strip_whitespace in de modelconfiguratie, dus "   " telt ook als leeg;
# tekst met alleen onzichtbare tekens (bijv. een zero-width space of een nulbyte) ook.
NonEmptyText = Annotated[str, Field(min_length=1), AfterValidator(_require_visible_text)]

# Modelconfiguratie voor alle modellen in dit formaat:
# - extra="forbid": onbekende velden worden geweigerd;
# - validate_assignment: ook een toewijzing na constructie wordt gevalideerd
#   (anders kan bijv. NaN of een gevulde constructieve_parameters er alsnog in);
# - revalidate_instances="always": een al gemaakt (en daarna mogelijk aangepast)
#   object wordt opnieuw gecontroleerd als het in een ander model wordt gezet.
_STRICT_MODEL = {"extra": "forbid", "validate_assignment": True, "revalidate_instances": "always"}


# Plek van een getal op de tekening, in de eenheid van de bron:
# PDF-punten (pt) voor vector-PDF, pixels (px) voor een scan. Pagina is 1-gebaseerd.
class Position(BaseModel):
    model_config = ConfigDict(**_STRICT_MODEL)

    pagina: int = Field(ge=1)
    x: FiniteFloat
    y: FiniteFloat
    eenheid: PositionUnit


# Herkomst van een getal: welk soort bron en welk bestand
class Source(BaseModel):
    model_config = ConfigDict(**_STRICT_MODEL, str_strip_whitespace=True)

    type: SourceType
    bestand: NonEmptyText
    toelichting: str | None = None


# Eén uitgelezen getal met waarde (mm), positie, richting, bron en betrouwbaarheid
class Measurement(BaseModel):
    model_config = ConfigDict(**_STRICT_MODEL, str_strip_whitespace=True)

    id: NonEmptyText
    waarde: FiniteFloat | None
    eenheid: Literal["mm"] = "mm"
    positie: Position | None = None
    richting: Direction | None = None
    bron: Source
    betrouwbaarheid: ReliabilityLabel
    onderbouwing: str | None = None
    ruwe_tekst: str | None = None

    # Consistentie tussen label en waarde: 'ontbreekt' als en slechts als er geen waarde is,
    # en 'bewezen' alleen met een niet-lege onderbouwing. Het label zelf bepalen hoort bij S1.4.
    @model_validator(mode="after")
    def check_label_consistency(self) -> "Measurement":
        if self.betrouwbaarheid == "ontbreekt" and self.waarde is not None:
            raise ValueError("label 'ontbreekt' mag geen waarde hebben")
        if self.betrouwbaarheid != "ontbreekt" and self.waarde is None:
            raise ValueError(
                f"label '{self.betrouwbaarheid}' vereist een waarde; gebruik 'ontbreekt'"
            )
        if self.betrouwbaarheid == "bewezen" and not _has_visible_text(self.onderbouwing):
            raise ValueError("label 'bewezen' vereist een niet-lege onderbouwing")
        return self


# Het tussenformaat van één verwerkte tekening
class ExtractionResult(BaseModel):
    model_config = ConfigDict(**_STRICT_MODEL)

    formaat_versie: Literal["0.1"] = FORMAT_VERSION
    maten: list[Measurement] = Field(default_factory=list)

    # Gereserveerde plek voor constructieve parameters (Backlog "Buiten scope voor nu", L5).
    # Bewust niet ingevuld en altijd null: zo kan het formaat later worden uitgebreid
    # zonder bestaande velden te hernoemen, en zet geen route er stilzwijgend iets in.
    constructieve_parameters: None = None

    # Elke maat moet binnen één resultaat aanwijsbaar zijn (bijv. in een maatketen, S1.4)
    @model_validator(mode="after")
    def check_unique_ids(self) -> "ExtractionResult":
        seen: set[str] = set()
        for measurement in self.maten:
            if measurement.id in seen:
                raise ValueError(f"dubbele id in maten: '{measurement.id}'")
            seen.add(measurement.id)
        return self

    # JSON-(de)serialisatie voor tests en bewijs; geen uitvoerformaat (dat is S1.6).
    # to_json valideert eerst het hele object opnieuw: wijzigingen die validate_assignment
    # niet ziet (bijv. maten.append(...), een id in een bestaande maat dubbel maken,
    # model_copy(update=...)) leveren zo een fout op in plaats van JSON die from_json
    # weigert of, erger, een NaN die stil als null wordt weggeschreven.
    def to_json(self) -> str:
        validated = type(self).model_validate(self.model_dump(warnings=False))
        return validated.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, data: str) -> "ExtractionResult":
        return cls.model_validate_json(data)
