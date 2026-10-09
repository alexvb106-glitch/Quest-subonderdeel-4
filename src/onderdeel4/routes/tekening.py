from fastapi import APIRouter, Depends, Request, status

from onderdeel4.auth import require_api_key
from onderdeel4.errors import ApiError
from onderdeel4.job_store import InMemoryJobStore
from onderdeel4.schemas import (
    ErrorResponse,
    JobCreatedResponse,
    JobStatusResponse,
    TekeningRequest,
)

# Router voor /tekening; de API-key-controle geldt voor alle endpoints hierin
router = APIRouter(
    prefix="/tekening",
    tags=["tekening"],
    dependencies=[Depends(require_api_key)],
    responses={
        401: {"model": ErrorResponse, "description": "API-key ontbreekt of is ongeldig"},
        422: {"model": ErrorResponse, "description": "Ongeldige invoer"},
        500: {"model": ErrorResponse, "description": "Interne fout of API-key niet geconfigureerd"},
    },
)


# Haal de job-opslag op die bij de app hoort (gezet in create_app)
def get_job_store(request: Request) -> InMemoryJobStore:
    return request.app.state.job_store


# Start een nieuwe job. Zonder routelogica blijft de job op "processing" staan (skeleton).
@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=JobCreatedResponse,
    summary="Start een nieuwe tekening-job",
)
def create_tekening_job(
    body: TekeningRequest, job_store: InMemoryJobStore = Depends(get_job_store)
) -> JobCreatedResponse:
    job = job_store.create(body.model_dump())
    return JobCreatedResponse(job_id=job.job_id, status=job.status)


# Vraag de status en (later) het resultaat van een job op
@router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    summary="Vraag de status van een tekening-job op",
    responses={404: {"model": ErrorResponse, "description": "Job niet gevonden"}},
)
def get_tekening_job(
    job_id: str, job_store: InMemoryJobStore = Depends(get_job_store)
) -> JobStatusResponse:
    job = job_store.get(job_id)
    if job is None:
        raise ApiError(404, "job_niet_gevonden", "Er bestaat geen job met dit job_id.")
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        tekening_referentie=job.tekening_referentie,
        gebruikte_route=job.gebruikte_route,
        foutmelding=job.foutmelding,
    )
