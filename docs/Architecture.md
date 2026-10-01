# ARCHITECTURE.md
### QUEST — Onderdeel 4 — Automatiseren bouwtekeningen

> **Status:** v0.3 — concept, opgesteld in overleg met Alex van Bommel.
> **Datum:** 1 oktober 2026 (§4 bijgewerkt — eerder v0.2, 25 september 2026)
> **Let op:** dit onderdeel start met een individuele spike-week per teamlid (zie `CLAUDE.md` §3). Enkele technische keuzes hieronder zijn daarom nog voorlopig — definitief te maken ná die week, op basis van wat werkte.

---

## 1. Techstack

| Keuze | Status |
|---|---|
| Programmeertaal API/backend | **Python — bevestigd, teambreed besproken en vastgesteld (25-09-2026).** |
| PDF-verwerking (route c) | `[OPEN]` Geen vaste aanpak — de te ontvangen archief-PDF's volgen geen vaste tekenstandaard (variëren per bouwperiode/gemeente), dus dit wordt per situatie/tijdens de spike verkend (OCR versus vectorisatie/beeldherkenning). |
| Conversie naar IFC/DXF | `[OPEN]` Te verkennen tijdens spike-week, bijv. `ifcopenshell` (IFC) of `ezdxf` (DXF) als startpunt — nog niet gekozen. |
| Dynamo-scripts (Alpha/Bravo-plaatsing) | Bestaand, werkend op Revit-projecten (zie `CLAUDE.md` §2) — dient als referentie voor plaatsings-/conversielogica, ook al is Revit niet langer de primaire route. |

`[LET OP]` Tijdens de spike-week verkennen Alex en Jeroen desondanks nog **bewust hun eigen aanpak** voor de PDF-verwerking en conversielogica binnen Python (zie `CLAUDE.md` §3) — de taalkeuze staat vast, de precieze libraries/techniek per route nog niet.

**Argumentatie voor het uitstellen van PDF-verwerking/conversie:** de input (archief-PDF's) verschilt sterk per bouwperiode en gemeente, zonder vaste tekenstandaard. Eén aanpak vooraf kiezen zonder deze variatie gezien te hebben, zou een eerste-de-beste-keuze zijn in plaats van een onderbouwde. De argumentatie komt er wél, alleen pas ná de verkenning i.p.v. vooraf.

---

## 2. API-ontwerp

### 2.1 Verwerkingsmodel: asynchroon (job-queue)

Gekozen voor **asynchrone verwerking via een job-queue**, niet synchrone request/response. Argumentatie:
- Archiefonderzoek + conversie kan langer duren dan een normale HTTP-timeout toelaat.
- Er moeten soms **meerdere PDF's van hetzelfde pand of dezelfde verdieping** worden ingeladen en gecombineerd (zie antwoord B4) — dat past niet in één simpel request/response-patroon.

`[OPEN — te bepalen tijdens spike-week]` Concrete implementatie van de job-queue. Twee realistische opties op PoC-niveau (§ afwerkingsniveau, `CLAUDE.md` §8), zonder zware infrastructuur zoals een aparte Redis-server:
- **Optie 1 — Huey met SQLite-backend:** lichte taakwachtrij, geen aparte queue-server nodig, past bij "nu lokaal" (antwoord D8).
- **Optie 2 — eigen jobtabel + achtergrondproces:** een simpele tabel (`job_id`, `status`, `created_at`, ...) in combinatie met een eenvoudige worker (bijv. Python `threading`/`multiprocessing`), zonder extra library.

Beide zijn te verkiezen boven Celery+Redis, wat voor dit onderdeel waarschijnlijk overgedimensioneerd is gezien het afwerkingsniveau.

### 2.2 Endpoints (voorstel, nog niet gevalideerd met onderdeel 5)

| Endpoint | Methode | Omschrijving |
|---|---|---|
| `/tekening` | `POST` | Start een nieuwe job. Input: building-referentie of adres, optioneel voorkeursroute, optioneel bestand(en) (PDF's / Revit-bestand voor route b/c). Response: `202 Accepted` + `job_id`. |
| `/tekening/{job_id}` | `GET` | Vraagt status/resultaat van een job op: `processing`, `done`, `failed` + (bij `done`) tekening-referentie en gebruikte route. |

`[OPEN]` Of bestandsupload (route b/c) via dit onderdeel se eigen API loopt, of via onderdeel 5's interface — zie `CLAUDE.md` §9, nog te bespreken met onderdeel 5 (samenhangt met F14 uit eerder gesprek: nog niet bepaald).

### 2.3 Authenticatie en foutafhandeling

- API-key per aanroep, via header (bijv. `X-API-Key`), opgeslagen als environment variable — **nooit in de repo**, conform `Onderdeel5_Interfaces_voorstel.md` §1.
- Foutresponses als JSON met een duidelijke status/foutcode en leesbare boodschap, conform het generieke afsprakenkader uit `Onderdeel5_Interfaces_voorstel.md` §1.

### 2.4 Formaat

JSON voor alle request/response-verkeer, conform het generieke afsprakenkader uit `Onderdeel5_Interfaces_voorstel.md` §1. Geen reden gevonden om hiervan af te wijken.

---

## 3. Datamodel

**Ja, dit onderdeel heeft een eigen, licht datamodel nodig** — niet stateless, vanwege de asynchrone verwerking.

| Tabel (v0.2) | Velden (concept) |
|---|---|
| `jobs` | `job_id`, `building_referentie`/`adres`, `route` (a/b/c), `status`, `resultaat_referentie`, `aangemaakt_op`, `afgerond_op`, `foutmelding` (indien van toepassing) |

**Besluit — geen cache van archiefbronnen in v0.2.** Bewust niet toegevoegd: de meerwaarde (minder herhaald zoekwerk) is pas relevant bij meerdere gebouwen binnen dezelfde gemeente, en dat scenario doet zich in de projectperiode vermoedelijk niet voor (één representatief testgebouw per bouwperiode, zie PvA deelproduct 4). Toevoegen zou complexiteit oplossen voor een probleem dat er nog niet is. Opgenomen als **"Later"-prioriteit in `Backlog.md`**, te heractiveren zodra testen uitwijst dat een archiefbron traag of rate-limited is.

Aanbevolen opslag op dit afwerkingsniveau: **SQLite** — geen aparte databaseserver nodig, past bij "nu lokaal" en PoC-niveau.

---

## 4. Repo- en mapstructuur

`[BIJGEWERKT v0.3 — 1 oktober 2026]` Aangevuld met `.claude/plans/`, dat er bij het opzetten van de repo (S0.1) bij bleek te horen maar nog niet in v0.2 stond: dit is waar de `planner`-subagent de planbestanden per slice neerzet (status `draft` → `approved` → `in_uitvoering` → `gereviewd`, zie `Workflow.md` §2). De repo staat inmiddels live op GitHub (`alexvb106-glitch/Quest-subonderdeel-4`), met de vier subagents (`planner`, `builder`, `reviewer`, `breker`) en de zeven slash-commands al aangemaakt in `.claude/agents/` resp. `.claude/commands/`.

```
onderdeel-4/
├── .claude/
│   ├── agents/       # planner.md, builder.md, reviewer.md, breker.md
│   ├── commands/     # de zeven slash-commands (zie Workflow.md §1)
│   └── plans/        # planbestanden per slice, aangemaakt door /nieuwe-slice
├── docs/             # CLAUDE.md, Architecture.md, Interfaces.md, Design.md, Backlog.md, Huisstijl_en_conventies.md
├── src/              # applicatiecode
├── tests/
├── .gitignore
├── CLAUDE.md         # in de root
└── README.md
```

Repo is door onderdeel 4 zelf aangemaakt (niet centraal door Kai), conform `CLAUDE.md` §7. Pushen naar GitHub gebeurt bewust handmatig door het teamlid zelf (human in the loop), niet geautomatiseerd — zie ook de instructie in `.claude/commands/github-afronding.md`.

---

## 5. Hosting / omgeving

`[VOORLOPIG]` Draait nu lokaal (antwoord D8). Nog niet bepaald waar dit uiteindelijk draait (Inside Out-infra, VM, anders) — relevant zodra route (b) (Revit-stub) ooit praktisch uitgewerkt zou worden, aangezien Revit een Windows-omgeving met licentie vereist. Geen actie nodig zolang dit lokaal blijft; wel iets om te agenderen zodra er richting productie/demo wordt gewerkt.

---

## 6. Gerelateerde documenten

| Document | Relevantie voor dit document |
|---|---|
| `CLAUDE.md` | Scope, routes, afwerkingsniveau, open punten richting onderdeel 5 |
| `Onderdeel5_Interfaces_voorstel.md` | Generiek afsprakenkader (auth, JSON, foutafhandeling); §5 nog aan te passen na Revit-scopewijziging |
| `Interfaces.md` (onderdeel 4) | Eigen versie van het contract, gebaseerd op dit document |
| `Workflow.md` | Procesdraaiboek dat tegen deze architectuur getest wordt (o.a. door de breker) |
| `Backlog.md` | Bevat o.a. de "Later"-slice voor archiefbron-caching (zie §3) |
