"""Tussenformaat voor uitgelezen maten (slice S1.1).

Beide routes (vector-PDF en scan) schrijven naar dit formaat; de controle (S1.4)
en de uitvoer (S1.6) lezen eruit. Dit bestand bevat alleen de datastructuur en
consistentiebewaking, geen detectie, controle of uitvoer.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

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

# Niet-lege tekst (na het weghalen van witruimte aan de randen)
NonEmptyText = Annotated[str, Field(min_length=1)]


# Plek van een getal op de tekening, in de eenheid van de bron:
# PDF-punten (pt) voor vector-PDF, pixels (px) voor een scan. Pagina is 1-gebaseerd.
class Position(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pagina: int = Field(ge=1)
    x: FiniteFloat
    y: FiniteFloat
    eenheid: PositionUnit


# Herkomst van een getal: welk soort bron en welk bestand
class Source(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    type: SourceType
    bestand: NonEmptyText
    toelichting: str | None = None


# Eén uitgelezen getal met waarde (mm), positie, richting, bron en betrouwbaarheid
class Measurement(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

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
        if self.betrouwbaarheid == "bewezen" and not self.onderbouwing:
            raise ValueError("label 'bewezen' vereist een niet-lege onderbouwing")
        return self


# Het tussenformaat van één verwerkte tekening
class ExtractionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

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

    # JSON-(de)serialisatie voor tests en bewijs; geen uitvoerformaat (dat is S1.6)
    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, data: str) -> "ExtractionResult":
        return cls.model_validate_json(data)
