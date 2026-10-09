# Onderdeel 4 — Automatiseren bouwtekeningen

QUEST — Interactieve VvE-Configurator voor Verduurzaming van Hoogbouw (Inside Out).

Koppelt een gezocht gebouw aan een bruikbare bouwtekening, zodat onderdeel 5 kan tonen of io Alpha en io Bravo op het gebouw passen.

## Documentatie

Zie `CLAUDE.md` (root) voor scope, routes en teamafspraken, en `docs/` voor de volledige documentenset:

- `docs/Architecture.md` — techstack, API-ontwerp, datamodel
- `docs/Interfaces.md` — contract met onderdeel 1 en onderdeel 5
- `docs/Design.md` — interface-status (geen eigen UI)
- `docs/Backlog.md` — sliceplanning
- `docs/Workflow.md` — het slice-draaiboek (`.claude/`-commands)
- `docs/Huisstijl_en_conventies.md` — projectbrede conventies

## Lokaal draaien

Vereist Python 3.14 (zie `.python-version`). Voorbeelden in PowerShell, vanuit de root van de repo.

```powershell
# Virtuele omgeving aanmaken en activeren
python -m venv .venv
.venv\Scripts\Activate.ps1

# Dependencies installeren (runtime + test)
pip install fastapi uvicorn pytest httpx

# API-key zetten voor deze sessie (eigen waarde kiezen, nooit in de repo zetten)
$env:ONDERDEEL4_API_KEY = "<jouw-api-key>"

# API starten
uvicorn onderdeel4.main:app --app-dir src
```

De interactieve API-documentatie staat daarna op <http://127.0.0.1:8000/docs> (bereikbaar zonder API-key). De endpoints onder `/tekening` vereisen de header `X-API-Key` met dezelfde waarde als `ONDERDEEL4_API_KEY`.

Tests draaien: `python -m pytest`.

## Status

Fase 0 — fundament; spike-week afgerond.
