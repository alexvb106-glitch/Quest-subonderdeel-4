from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Maximale lengte van tekstvelden in de invoer (PoC-niveau, aanname 10 in het S0.3-plan)
MAX_TEXT_LENGTH = 200

Route = Literal["a", "b", "c"]
JobStatus = Literal["processing", "done", "failed"]


# Adres als alternatief voor building_referentie (Interfaces.md §1).
# huisnummer is tekst, zodat toevoegingen als "12A" passen.
class Adres(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    straat: str = Field(min_length=1, max_length=MAX_TEXT_LENGTH)
    huisnummer: str = Field(min_length=1, max_length=MAX_TEXT_LENGTH)
    postcode: str = Field(min_length=1, max_length=MAX_TEXT_LENGTH)
    plaats: str = Field(min_length=1, max_length=MAX_TEXT_LENGTH)


# Invoer voor POST /tekening. Geen bestandsveld: upload is nog een open punt
# (Architecture.md §2.2), daarom worden onbekende velden geweigerd.
class TekeningRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    building_referentie: str | None = Field(
        default=None, min_length=1, max_length=MAX_TEXT_LENGTH
    )
    adres: Adres | None = None
    voorkeursroute: Route | None = None

    # Minstens één identificatieveld is verplicht
    @model_validator(mode="after")
    def check_identification(self) -> "TekeningRequest":
        if self.building_referentie is None and self.adres is None:
            raise ValueError("geef minstens building_referentie of adres mee")
        return self


# Antwoord bij het aanmaken van een job (202 Accepted)
class JobCreatedResponse(BaseModel):
    job_id: str
    status: JobStatus


# Antwoord bij het opvragen van een job (Interfaces.md §2)
class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    tekening_referentie: str | None = None
    gebruikte_route: Route | None = None
    foutmelding: str | None = None


# Foutformaat, alleen voor de OpenAPI-documentatie (de echte opbouw zit in errors.py)
class ErrorDetail(BaseModel):
    status: int
    code: str
    boodschap: str


class ErrorResponse(BaseModel):
    fout: ErrorDetail
