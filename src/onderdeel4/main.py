from fastapi import FastAPI

from onderdeel4.errors import register_exception_handlers
from onderdeel4.job_store import InMemoryJobStore
from onderdeel4.routes.tekening import router as tekening_router


# Bouw de applicatie: metadata voor /docs, foutafhandeling, job-opslag en routes
def create_app() -> FastAPI:
    app = FastAPI(
        title="QUEST onderdeel 4 - Automatiseren bouwtekeningen",
        description=(
            "Koppelt een gezocht gebouw aan een bruikbare bouwtekening. "
            "Alle /tekening-endpoints vereisen een geldige API-key in de header X-API-Key."
        ),
        version="0.1.0",
    )
    register_exception_handlers(app)
    app.state.job_store = InMemoryJobStore()
    app.include_router(tekening_router)
    return app


# Module-level app voor uvicorn: uvicorn onderdeel4.main:app --app-dir src
app = create_app()
