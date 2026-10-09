import unicodedata
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

# Maximale lengte van tekstvelden in de invoer (PoC-niveau, aanname 10 in het S0.3-plan)
MAX_TEXT_LENGTH = 200


# Weiger controletekens (bijv. null bytes, escape-codes, regeleinden) in tekstvelden:
# die horen niet in een referentie of adres en geven later problemen bij opslag en logging
def _reject_control_characters(value: str) -> str:
    if any(unicodedata.category(char) == "Cc" for char in value):
        raise ValueError("bevat ongeldige (controle)tekens")
    return value


# Tekstveld voor de invoer: niet leeg, begrensde lengte, geen controletekens
InputText = Annotated[
    str,
    Field(min_length=1, max_length=MAX_TEXT_LENGTH),
    AfterValidator(_reject_control_characters),
]

# Toegestane routes en job-statussen (Interfaces.md §1 en §2)
Route = Literal["a", "b", "c"]
JobStatus = Literal["processing", "done", "failed"]


# Adres als alternatief voor building_referentie (Interfaces.md §1).
# huisnummer is tekst, zodat toevoegingen als "12A" passen.
class Adres(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    straat: InputText
    huisnummer: InputText
    postcode: InputText
    plaats: InputText


# Invoer voor POST /tekening. Geen bestandsveld: upload is nog een open punt
# (Architecture.md §2.2), daarom worden onbekende velden geweigerd.
class TekeningRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    building_referentie: InputText | None = None
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


# Omhulsel {"fout": {...}} rond de foutdetails, zoals in elke foutresponse
class ErrorResponse(BaseModel):
    fout: ErrorDetail
