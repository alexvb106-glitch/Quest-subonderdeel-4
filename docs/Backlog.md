# BACKLOG.md
### QUEST — Onderdeel 4 — Automatiseren bouwtekeningen

> **Status:** v0.3 — concept, bijgewerkt na de spike-week in overleg met Alex van Bommel. Fase 1 is nog te bevestigen door Jeroen van Leening.
> **Datum:** 9 oktober 2026 (S1.3 bijgewerkt na keuze PDF-library — eerder v0.2, 7 oktober 2026; v0.1, 25 september 2026)
> **MVP-definitie (bevestigd):** zicht op alle drie de routes (a, b, c) — ook als er maar één volledig end-to-end uitgewerkt is, moet voor de andere twee minstens een onderbouwde haalbaarheidsinschatting liggen. Dit sluit aan bij PvA deelproduct 4.

`[GEWIJZIGD v0.2]` S0.2 is afgesloten, Fase 1 is ingevuld op basis van `Spike_overdracht.md`, en de afhankelijkheden zijn aangepast aan de daar voorgestelde volgorde (de routes hangen niet langer af van de job-queue). S0.1 is bijgewerkt na controle van de repo.

---

## Buiten scope voor nu

**Constructieve parameters** — dragende wanden, ketelhuis of technische ruimte, draagvermogen van het dak. Alex vraagt bij Olivier (Inside Out) na of de tool dit moet behandelen of dat het bij de VvE of een constructieadviseur blijft. Tot dat antwoord er is: niet bouwen en niet ontwerpen. Het tussenformaat (S1.1) laat er alleen ruimte voor.

---

## Uitvoervolgorde

S0.1 → S0.3 → S1.1 → S1.2 → S1.3 → S1.4 → S1.5 → S1.6 → S0.4 → S2.1 en S2.2 → S1.7 → S1.8

---

## Fase 0 — Fundament

| Slice | Naam | Beschrijving | Prioriteit | Afhankelijk van | Status |
|---|---|---|---|---|---|
| S0.1 | Repo & scaffolding | De repo-structuur conform `Architecture.md` §4 afmaken. Nog te doen: (1) Python 3.14.7 vastleggen in `.python-version`, en `pyproject.toml` met `requires-python = ">=3.14"`; (2) testbasis: `pytest` als enige dependency (ontwikkel-dependency), pytest-configuratie in `pyproject.toml` en één eerste test in `tests/` die slaagt; (3) `.claude/plans/.gitkeep`, omdat git geen lege mappen bewaart; (4) `docs/Spike_overdracht.md` toevoegen; (5) status in `README.md` bijwerken naar "Fase 0 — fundament; spike-week afgerond". Runtime-dependencies horen niet in deze slice: elke library komt erbij in de slice die haar voor het eerst nodig heeft. | MVP | — | Afgerond (PR #1, gemerged 7-10-2026). |
| S0.2 | Individuele spike-week verkenning | Alex en Jeroen verkenden ieder een week dezelfde probleemstelling vanuit een eigen aanpak. | MVP | — | **Afgerond (7-10-2026).** Uitkomst: `Spike_overdracht.md`. Spike-code is wegwerpcode en gaat niet mee naar de repo. |
| S0.3 | API- en authenticatielaag | Basis API-service (Python) met API-key-authenticatie via environment variable en generieke JSON-foutafhandeling, conform `Interfaces.md` §3. Nog zonder routelogica — alleen het skeleton met `/tekening` en `/tekening/{job_id}` volgens `Architecture.md` §2.2. | MVP | S0.1 | Open. Webframework: FastAPI (besloten 9-10-2026, zie `Architecture.md` §1). |
| S0.4 | Job-queue opzetten | Asynchrone verwerking implementeren (`Architecture.md` §2.1 — Huey+SQLite of eigen jobtabel + achtergrondproces). `jobs`-tabel conform `Architecture.md` §3. | MVP | S0.3, minstens één werkende route (S1.3) | Open. `[OPEN]` De keuze tussen de twee opties stond op "na S0.2", maar de spike heeft hier niets over opgeleverd. Te beslissen bij het plannen van deze slice. |

---

## Fase 1 — Routes

Gebaseerd op de spike-bevindingen: maten komen uit getallen en vorm uit lijnen, en de controle staat los van de detectie.

| Slice | Naam | Beschrijving | Prioriteit | Afhankelijk van | Status |
|---|---|---|---|---|---|
| S1.1 | Tussenformaat en betrouwbaarheidslabels | Eén datastructuur per uitgelezen getal: waarde, positie, richting, bron en betrouwbaarheid. Eén set labels: `bewezen`, `onzeker`, `ontbreekt`. Beide routes schrijven naar dit formaat. Laat ruimte voor constructieve parameters, zonder ze in te vullen. | MVP | S0.1 | Open |
| S1.2 | Ingang: vector of scan | Eén ingang die van een aangeleverd PDF-bestand bepaalt of het een vector-PDF of een scan is, en het doorstuurt naar de juiste route. Onbekende of corrupte bestanden geven een duidelijke fout. | MVP | S1.1 | Open |
| S1.3 | Route (c) — vector-PDF | Tekst met positie uit de PDF lezen (aanpak Jeroen, in de spike met PyMuPDF; om te zetten naar pdfplumber, zie `Architecture.md` §1) en als maten in het tussenformaat zetten. Testtekening: Naxosdreef, schaal 1:100. Verwachte waarden uit de spike: breedte 25370 mm, diepte 9860 mm. | MVP | S1.2 | Open. AGPL-punt van PyMuPDF vervallen: het team koos op 9-10-2026 voor pdfplumber (MIT). |
| S1.4 | Onafhankelijke controle (optelsom) | Maatketens optellen en vergelijken met de totaalmaat, draaiend op het tussenformaat en los van de detectiecode. Bepaalt het label per waarde. Bruikbaar voor beide routes. | MVP | S1.1, S1.3 | Open |
| S1.5 | Route (c) — scan | Dakomtrek en dakopbouwen uit het beeld halen (aanpak Alex, OpenCV). Maten worden met de hand ingevoerd; OCR is niet getest. Aparte ijking per richting, omdat een oude scan niet maatvast is (3,6% verschil). Testtekening: Theemsdreef 1964. Kleine obstakels krijgen label `onzeker`. | MVP | S1.2, S1.4 | Open. `[OPEN]` Hoe de tool zelf het juiste deel van een blad vindt; in de spike waren zoekvensters en drempels handwerk. |
| S1.6 | Uitvoer | Uit het tussenformaat genereren: JSON voor onderdeel 5, DXF voor de geometrie, een leesbaar rapport en een bewijsbestand per uitkomst. Het rapport is verplicht: het laat Inside Out-medewerkers zien wat de tool deed en hoe hij de tekening analyseerde. De vorm ligt niet vast (het spike-rapport van Alex is alleen een voorbeeld). | MVP | S1.3 (uit te breiden na S1.5) | Open. `[OPEN]` Uitvoerformaat IFC of DXF staat nog open in `CLAUDE.md` §1; de spike wijst naar DXF. |
| S1.7 | Route (a) — archiefonderzoek, haalbaarheid | Vaststellen of een archiefbron geautomatiseerd doorzoekbaar is en of de gevonden tekening bij het juiste pand hoort. Het adres in het titelblok is leidend, niet de zoekterm. De uitkomst mag negatief zijn; oplevering is dan een onderbouwde haalbaarheidsinschatting. | MVP (als haalbaarheidsbewijs) | S1.3 | Open |
| S1.8 | Route (b) — Revit-stub | Voorbereide, niet uitgewerkte ingang voor het geval dat een VvE zelf een Revit-bestand aanlevert. | MVP (als haalbaarheidsbewijs) | S0.3 | Open. `[OPEN]` Upload via onderdeel 4 of via onderdeel 5, zie `CLAUDE.md` §9. |

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
| L1 | Archiefbron-caching | Cache van eerder gevonden archiefbronnen per gemeente, om herhaald zoekwerk te besparen. Bewust niet in MVP — zie onderbouwing in `Architecture.md` §3. | Later | S1.7 | Open — heractiveren bij signaal van trage/rate-limited archiefbron |
| L2 | Interne testpagina | Alleen indien tijdens ontwikkeling blijkt dat een visuele check nodig is (job-statussen bekijken, tekening previewen). Eigen, expliciete slice — nooit stilzwijgend meegebouwd, zie `Design.md` §2. | Later | — | Open, alleen bij aantoonbare behoefte |
| L3 | 3DBAG als onafhankelijke controle | Uitgelezen dakmaten vergelijken met de 3DBAG-geometrie van hetzelfde pand, als externe controle en vangnet. | Later `[OPEN — mogelijk MVP]` | S1.4, S2.3 | Open. In de spike gebruikte niemand een externe bron. |
| L4 | OCR op maatcijfers | Geschreven en handgeschreven maten automatisch uitlezen in de scanroute, in plaats van overtypen. | Later | S1.5 | Open. Niet getest in de spike. |
| L5 | Constructieve parameters | Dragende wanden, technische ruimte, draagvermogen dak. | Buiten scope | Antwoord van Olivier | Geparkeerd, zie "Buiten scope voor nu" |

---

## Open punten vóór de eerste slice

- [ ] Fase 1 en het samenvoegbesluit bevestigen met Jeroen
- [x] Eén Python-versie afspreken: 3.14.7 (besloten door Alex, 7-10-2026). Alex en Jeroen werken beiden op 3.14.7 (bevestigd 7-10-2026).
- [ ] PvA deelproduct 4 aanpassen: de aanname van recente tekeningen klopt niet meer
- [ ] Reviewer- en breker-instructie aanscherpen: in de spike liet de AI drie keer een controle slagen die niet was uitgevoerd
- [ ] Antwoord van Olivier over de constructie vastleggen zodra het er is

---

## Gerelateerde documenten

| Document | Relevantie voor dit document |
|---|---|
| `CLAUDE.md` | Scope, routes, spike-week-afspraak (§3), afwerkingsniveau (§8) |
| `Architecture.md` | Techstack, API-ontwerp, datamodel — basis voor de meeste slices |
| `Interfaces.md` | Contract met onderdeel 1 en 5 — basis voor Fase 2 |
| `Design.md` | Reden waarom L2 pas bij aantoonbare behoefte gebouwd wordt |
| `Workflow.md` | Het slice-draaiboek waarmee elke slice hierboven wordt uitgevoerd |
| `Spike_overdracht.md` | Uitkomst van S0.2 — basis voor Fase 1 en de uitvoervolgorde |
