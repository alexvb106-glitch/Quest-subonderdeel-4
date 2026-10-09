import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


# Eigen foutklasse voor fouten die bewust met een code en boodschap worden teruggegeven
class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


# Het ene JSON-foutformaat voor alle foutresponses (aanname 5 in het S0.3-plan).
# Wijkt het formaat van onderdeel 5 af, dan is het alleen hier aan te passen.
def error_response(
    status: int, code: str, message: str, headers: dict[str, str] | None = None
) -> JSONResponse:
    body = {"fout": {"status": status, "code": code, "boodschap": message}}
    return JSONResponse(status_code=status, content=body, headers=headers)


# Vertaling van veelvoorkomende Pydantic-fouttypes naar een leesbare Nederlandse omschrijving
_VALIDATION_MESSAGES = {
    "missing": "verplicht veld ontbreekt",
    "extra_forbidden": "onbekend veld, niet toegestaan",
    "literal_error": "ongeldige waarde",
    "string_type": "moet tekst zijn",
    "string_too_short": "mag niet leeg zijn",
    "string_too_long": "is te lang",
    "model_attributes_type": "moet een object zijn",
    "dict_type": "moet een object zijn",
    "json_invalid": "ongeldige JSON",
}

# Grenzen voor de foutboodschap. Veldnamen in de locatie kunnen van de aanroeper komen
# (onbekende extra velden), dus nooit onbegrensd of ongefilterd terugsturen.
MAX_LOCATION_LENGTH = 50
MAX_REPORTED_ERRORS = 5


# Maak een locatie veilig om terug te sturen: alleen printbare tekens, en ingekort
def _safe_location(location: str) -> str:
    cleaned = "".join(char if char.isprintable() else "?" for char in location)
    if len(cleaned) > MAX_LOCATION_LENGTH:
        cleaned = cleaned[:MAX_LOCATION_LENGTH] + "..."
    return cleaned


# Bouw uit de lijst met validatiefouten één leesbare boodschap
def _format_validation_errors(exc: RequestValidationError) -> str:
    parts = []
    errors = exc.errors()
    for error in errors[:MAX_REPORTED_ERRORS]:
        # Locatie zonder het generieke voorvoegsel "body", bijv. "adres.postcode"
        location = ".".join(str(item) for item in error.get("loc", ()) if item != "body")
        location = _safe_location(location)
        error_type = error.get("type", "")
        # Bij kapotte JSON is de "locatie" een tekenpositie, geen veldnaam: weglaten
        if error_type == "json_invalid":
            location = ""
        if error_type == "value_error":
            # Eigen validatieregels (bijv. "minstens één identificatieveld") leveren zelf de tekst
            description = str(error.get("ctx", {}).get("error", "ongeldige waarde"))
        else:
            description = _VALIDATION_MESSAGES.get(error_type, "ongeldige waarde")
        if location:
            parts.append(f"{location}: {description}")
        elif error_type == "missing":
            parts.append("request body ontbreekt")
        else:
            parts.append(description)
    # Overige fouten alleen tellen, zodat de boodschap klein blijft
    remaining = len(errors) - MAX_REPORTED_ERRORS
    if remaining > 0:
        parts.append(f"en nog {remaining} andere fout(en)")
    return "De invoer is ongeldig: " + "; ".join(parts) + "."


# Codes en boodschappen voor generieke HTTP-fouten
# (onleesbare body zoals ongeldige UTF-8 of te diep geneste JSON, onbekend pad, verkeerde methode)
_HTTP_ERRORS = {
    400: ("ongeldig_verzoek", "De request body kon niet worden gelezen."),
    404: ("niet_gevonden", "Het opgevraagde pad bestaat niet."),
    405: ("methode_niet_toegestaan", "Deze HTTP-methode is niet toegestaan voor dit pad."),
}


# Registreer alle exception handlers op de app, zodat elke fout hetzelfde formaat krijgt
def register_exception_handlers(app: FastAPI) -> None:
    # Eigen fouten uit auth en routes
    @app.exception_handler(ApiError)
    async def handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
        return error_response(exc.status, exc.code, exc.message)

    # Ongeldige invoer (standaard-422 van FastAPI) in het eigen formaat
    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return error_response(422, "ongeldige_invoer", _format_validation_errors(exc))

    # Generieke HTTP-fouten van Starlette/FastAPI; headers (bijv. Allow bij 405) blijven behouden
    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code, message = _HTTP_ERRORS.get(
            exc.status_code, ("http_fout", "Het verzoek kon niet worden verwerkt.")
        )
        return error_response(exc.status_code, code, message, headers=exc.headers)

    # Onverwachte fouten: alleen serverside loggen, nooit details in de response
    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Onverwachte fout bij %s %s", request.method, request.url.path)
        return error_response(500, "interne_fout", "Er is een interne fout opgetreden.")
