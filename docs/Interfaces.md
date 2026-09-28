# INTERFACES.md
### QUEST — Onderdeel 4 — Automatiseren bouwtekeningen

> **Status:** v0.1 — concept, opgesteld in overleg met Alex van Bommel.
> **Datum:** 25 september 2026
> **Voor:** Claude Code (bouwt hiertegen met mockdata, zie §4, totdat de koppelingen met onderdeel 1 en onderdeel 5 bevestigd zijn).

---

## 1. Wat dit onderdeel ontvangt

**Van onderdeel 1 (3DBAG-koppeling), via onderdeel 5 of rechtstreeks — nog te bevestigen welke route:**

| Veld | Omschrijving |
|---|---|
| `building_referentie` | 3DBAG-id van het gezochte gebouw, indien al bekend. |
| `adres` | Alternatief op `building_referentie`: straat, huisnummer, postcode, plaats. |
| `voorkeursroute` *(optioneel)* | `a`, `b` of `c` — indien de gebruiker een route wil forceren; anders bepaalt dit onderdeel zelf de meest kansrijke route. |
| `bestand(en)` *(optioneel)* | Archief-PDF('s) of een bestaand Revit-bestand, bij route (c) resp. de uitzonderingsroute (b). |

`[OPEN]` Of dit onderdeel deze data rechtstreeks van onderdeel 1 ontvangt, of altijd via onderdeel 5 doorgegeven krijgt — nog niet bevestigd met onderdeel 1/5. Vooralsnog aangenomen: via onderdeel 5, analoog aan de trigger-beschrijving in `Onderdeel5_Interfaces_voorstel.md` §5.

`[OPEN — bewust open gelaten]` Of bestandsupload (route b/c) via dit onderdeel se eigen `/tekening`-endpoint loopt, of via onderdeel 5's interface met doorgifte aan dit onderdeel — zie `Architecture.md` §2.2 en `CLAUDE.md` §9. Dit wordt pas ingevuld ná overleg met onderdeel 5, niet hier al aangenomen.

---

## 2. Wat dit onderdeel teruggeeft

Aan onderdeel 5, per opgevraagde job:

| Veld | Omschrijving |
|---|---|
| `job_id` | Referentie naar de aangemaakte job (teruggegeven bij `POST /tekening`). |
| `status` | `processing`, `done` of `failed`. |
| `tekening_referentie` | Bij `status: done` — verwijzing naar het resultaat (bestand/URL). |
| `gebruikte_route` | `a`, `b` of `c` — welke route uiteindelijk gebruikt is. |
| `foutmelding` | Bij `status: failed` — leesbare boodschap + foutcode. |

Zie `Architecture.md` §2.2 voor de volledige endpoint-beschrijving (`POST /tekening`, `GET /tekening/{job_id}`).

---

## 3. Authenticatie en foutafhandeling

- **Authenticatie:** API-key per aanroep, via header (`X-API-Key`), opgeslagen als environment variable — nooit in de repo. Conform het generieke afsprakenkader in `Onderdeel5_Interfaces_voorstel.md` §1.
- **Foutafhandeling:** JSON-foutresponses met een duidelijke status/foutcode en leesbare boodschap. Onderdeel 5 toont hierop een begrijpelijke melding aan de eindgebruiker in plaats van te crashen.
- **Formaat:** JSON voor alle request/response-verkeer, geen uitzondering nodig voor dit onderdeel.

---

## 4. Mockdata-afspraak

Zolang de koppeling met onderdeel 1 (§1) én het uploadvraagstuk met onderdeel 5 (§1) niet bevestigd zijn, bouwt Claude Code tegen de contracten hierboven met gemockte responses — conform de projectbrede afspraak uit `Onderdeel5_Interfaces_voorstel.md` §1. Zodra een van beide bevestigd wordt, wordt dit document bijgewerkt en gaat de bijbehorende mock eruit.

---

## 5. Gerelateerde documenten

| Document | Relevantie voor dit document |
|---|---|
| `CLAUDE.md` | Scope, routes, open punten richting onderdeel 5 (§9) |
| `Architecture.md` | Endpoint-structuur, job-statusmodel, auth (§2) — basis van dit document |
| `Onderdeel5_Interfaces_voorstel.md` | Generiek afsprakenkader; §5 bevat onderdeel 5's oorspronkelijke voorstel, nog te herzien na Revit-scopewijziging |
| `Backlog.md` | Elke koppeling (met onderdeel 1, met onderdeel 5) wordt een eigen slice, met mock- en later live-versie |
