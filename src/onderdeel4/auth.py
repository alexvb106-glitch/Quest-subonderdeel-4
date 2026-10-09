import secrets

from fastapi import Security
from fastapi.security import APIKeyHeader

from onderdeel4.config import get_configured_api_key
from onderdeel4.errors import ApiError

# Header waarin de aanroeper de API-key meestuurt (Interfaces.md §3).
# auto_error=False: de foutafhandeling doen we zelf, in het eigen JSON-formaat.
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# Dependency die elke beveiligde request controleert op een geldige API-key
def require_api_key(provided_key: str | None = Security(api_key_header)) -> None:
    # Fail closed: zonder geconfigureerde sleutel komt niemand erin
    configured_key = get_configured_api_key()
    if configured_key is None:
        raise ApiError(
            500,
            "api_key_niet_geconfigureerd",
            "De API-key is op de server niet geconfigureerd.",
        )

    # Header ontbreekt of is leeg
    if not provided_key:
        raise ApiError(401, "api_key_ontbreekt", "De header X-API-Key ontbreekt.")

    # Vergelijking in constante tijd; als bytes, zodat ook niet-ASCII-invoer veilig vergeleken wordt
    if not secrets.compare_digest(provided_key.encode("utf-8"), configured_key.encode("utf-8")):
        raise ApiError(401, "api_key_ongeldig", "De meegegeven API-key is ongeldig.")
