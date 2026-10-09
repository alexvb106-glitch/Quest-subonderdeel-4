import os

# Naam van de environment variable waarin de API-key staat (nooit in de repo)
API_KEY_ENV_VAR = "ONDERDEEL4_API_KEY"


# Lees de geconfigureerde API-key per aanroep uit de environment,
# zodat er geen sleutel in een module-constante blijft hangen.
# Een lege of alleen-spaties-waarde geldt als "niet geconfigureerd".
def get_configured_api_key() -> str | None:
    value = os.environ.get(API_KEY_ENV_VAR, "").strip()
    return value or None
