# BACKLOG.md
### QUEST — Onderdeel 4 — Automatiseren bouwtekeningen

> **Status:** v0.1 — concept, opgesteld in overleg met Alex van Bommel.
> **Datum:** 25 september 2026
> **MVP-definitie (bevestigd):** zicht op alle drie de routes (a, b, c) — ook als er maar één volledig end-to-end uitgewerkt is, moet voor de andere twee minstens een onderbouwde haalbaarheidsinschatting liggen. Dit sluit aan bij PvA deelproduct 4: "we zullen aantonen dat minimaal 1 van de 3 zal koppelen... ons streven is om dit zo te maken dat alle 3 de soorten tekeningen mogelijk zijn."

---

## Fase 0 — Fundament

| Slice | Naam | Beschrijving | Prioriteit | Afhankelijk van | Status |
|---|---|---|---|---|---|
| S0.1 | Repo & scaffolding | `.claude/`, `docs/`, `src/`, `tests/`, `CLAUDE.md` in de root opzetten conform `Architecture.md` §4. | MVP | — | Open |
| S0.2 | Individuele spike-week verkenning | Alex en Jeroen verkennen **individueel, ieder één week**, dezelfde probleemstelling (gebouwreferentie/adres → bruikbare tekeningdata), elk vanuit een eigen hoek/aanpak — om na afloop te kunnen vergelijken wat werkte. Taal is Python (bevestigd), verdere techniek per persoon vrij. Kan parallel aan S0.1 lopen (eigen sandbox, nog geen gedeelde repo-afhankelijkheid). | MVP | — | Open |
| S0.3 | API- en authenticatielaag | Basis API-service (Python) met API-key-authenticatie via environment variable en generieke JSON-foutafhandeling, conform `Interfaces.md` §3. Nog zonder routelogica — alleen de "skeleton" + `/tekening` en `/tekening/{job_id}` volgens `Architecture.md` §2.2. | MVP | S0.1 | Open |
| S0.4 | Job-queue opzetten | Asynchrone verwerking implementeren (`Architecture.md` §2.1 — Huey+SQLite of eigen jobtabel + achtergrondproces, definitieve keuze na S0.2). `jobs`-tabel conform `Architecture.md` §3. | MVP | S0.3, inzichten uit S0.2 | Open |

---

## Fase 1 — Routes (na spike-week)

`[OPEN — te vullen na S0.2]` De concrete implementatie-slices per route (a, b, c) worden pas na de individuele verkenningsweek vastgesteld, op basis van wat daadwerkelijk werkte. Nu al gedetailleerde slices verzinnen zou giswerk zijn — in lijn met de stophook-filosofie uit `Workflow.md`. Te verwachten grofweg:

| Slice | Naam | Beschrijving | Prioriteit | Afhankelijk van | Status |
|---|---|---|---|---|---|
| S1.x | Route (c) — PDF-conversie, eerste werkende versie | Voor minimaal één representatieve archief-PDF: tekst/maten uitlezen en omzetten naar een bruikbare tekening. | MVP | S0.2, S0.4 | `[OPEN — invulling na spike]` |
| S1.y | Route (a) — archiefonderzoek | Geautomatiseerd doorzoeken van een gekozen archiefbron; haalbaarheid en betrouwbaarheid vaststellen. | MVP | S0.2, S0.4 | `[OPEN — invulling na spike]` |
| S1.z | Route (b) — Revit-stub | Voorbereide (niet volledig uitgewerkte) ingang voor het uitzonderingsgeval dat een VvE een eigen Revit-bestand aanlevert. | MVP (als haalbaarheidsbewijs, niet als volledige uitwerking) | S0.4 | `[OPEN — invulling na spike]` |

---

## Fase 2 — Koppelingen met andere onderdelen

| Slice | Naam | Beschrijving | Prioriteit | Afhankelijk van | Status |
|---|---|---|---|---|---|
| S2.1 | Koppeling met onderdeel 1 (mock) | Building-referentie/adres ontvangen via gemockte data, conform `Interfaces.md` §1. | MVP | S0.3 | Open |
| S2.2 | Koppeling met onderdeel 5 (mock) | `tekening_referentie`, `gebruikte_route`, `status` teruggeven via gemockte responses, conform `Interfaces.md` §2. | MVP | S0.3 | Open |
| S2.3 | Koppeling met onderdeel 1 (live) | Mock vervangen door echte koppeling, zodra bevestigd of dit rechtstreeks of via onderdeel 5 loopt (`Interfaces.md` §1, open punt). | MVP | S2.1, extern overleg | `[OPEN — wacht op extern overleg]` |
| S2.4 | Koppeling met onderdeel 5 (live) | Mock vervangen door echte koppeling; inclusief definitieve afspraak over bestandsupload route (b/c) — via onderdeel 4's eigen API of via onderdeel 5's interface (`CLAUDE.md` §9). | MVP | S2.2, extern overleg | `[OPEN — wacht op extern overleg]` |

---

## Later (bewust uitgesteld)

| Slice | Naam | Beschrijving | Prioriteit | Afhankelijk van | Status |
|---|---|---|---|---|---|
| L1 | Archiefbron-caching | Cache van eerder gevonden archiefbronnen per gemeente, om herhaald zoekwerk te besparen. Bewust niet in MVP — zie onderbouwing in `Architecture.md` §3. | Later | S1.y | Open — heractiveren bij signaal van trage/rate-limited archiefbron |
| L2 | Interne testpagina | Alleen indien tijdens ontwikkeling blijkt dat een visuele check nodig is (job-statussen bekijken, tekening previewen). Eigen, expliciete slice — nooit stilzwijgend meegebouwd, zie `Design.md` §2. | Later | — | Open, alleen bij aantoonbare behoefte |

---

## Gerelateerde documenten

| Document | Relevantie voor dit document |
|---|---|
| `CLAUDE.md` | Scope, routes, spike-week-afspraak (§3), afwerkingsniveau (§8) |
| `Architecture.md` | Techstack, API-ontwerp, datamodel — basis voor de meeste slices |
| `Interfaces.md` | Contract met onderdeel 1 en 5 — basis voor Fase 2 |
| `Design.md` | Reden waarom L2 pas bij aantoonbare behoefte gebouwd wordt |
| `Workflow.md` | Het slice-draaiboek waarmee elke slice hierboven wordt uitgevoerd |
