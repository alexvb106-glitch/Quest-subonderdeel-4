import threading
import uuid
from dataclasses import dataclass, field
from typing import Any

# TIJDELIJK: in-memory opslag van jobs, zonder database of queue.
# Wordt in slice S0.4 vervangen door de echte job-queue/jobtabel. De endpoints
# praten alleen met deze interface (create/get), zodat dat zonder routewijziging kan.


# Eén job met de ontvangen invoer en de huidige status
@dataclass(frozen=True)
class Job:
    job_id: str
    status: str
    request_data: dict[str, Any] = field(default_factory=dict)
    tekening_referentie: str | None = None
    gebruikte_route: str | None = None
    foutmelding: str | None = None


# Thread-safe opslag in een dict, afgeschermd met een lock
class InMemoryJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    # Maak een nieuwe job aan met een uuid4 als job_id en status "processing"
    def create(self, request_data: dict[str, Any]) -> Job:
        job = Job(job_id=str(uuid.uuid4()), status="processing", request_data=request_data)
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    # Haal een job op; None als het job_id onbekend is
    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)
