# WORKFLOW.md
### QUEST — Onderdeel 4 — het slice-draaiboek

> **Status:** v1.0
> **Voor:** Claude Code. Formaliseert de `.claude/`-scaffold (subagents `planner`/`builder`/`reviewer`/`breker` en de zeven slash-commands) tot een volledig draaiboek — overgenomen van onderdeel 5, met alleen de breker-instructie aangepast aan dit onderdeel (geen useraccounts/rollen hier, wel een API met sleutel).

---

## 1. Overzicht: de zeven commando's

| Commando | Subagent | Doel | Status-overgang |
|---|---|---|---|
| `/nieuwe-slice Sx` | `planner` | Stelt een plan op voor slice X, gebaseerd op `Backlog.md` | → `draft` |
| `/keur-plan-goed` | — | Eigenaar/team keurt het plan goed | `draft` → `approved` |
| `/bouw-slice` | `builder` | Voert het goedgekeurde plan uit (automode) | `approved` → `in_uitvoering` |
| `/controleer-slice` | `reviewer` | Onafhankelijke controle tegen Definition of Done + conventies | `in_uitvoering` → `gereviewd` |
| `/breek-site` | `breker` | Probeert actief het resultaat kapot te maken, fixt gevonden problemen direct | binnen `gereviewd`, vóór de PR |
| `/leg-uit` | — | Legt de huidige stand in gewone taal uit, on-demand | geen statuswijziging |
| `/github-afronding` | — | Opent de Pull Request | wacht op PR-review team (`CLAUDE.md`) |

---

## 2. Stap 1 — Planningsfase (`/nieuwe-slice Sx`)

- De `planner` leest de betreffende slice uit `Backlog.md`, plus `Architecture.md`, `Interfaces.md` en `Design.md` voor zover relevant.
- Output: een planbestand (status `draft`) met wat gebouwd gaat worden, welke bestanden worden aangeraakt, en welke aannames worden gedaan (bijv. mockdata voor nog niet bevestigde `Interfaces.md`-punten met andere onderdelen).
- **Stophook:** komt de planner iets tegen dat niet in `Backlog.md` staat, of een keuze die eerst overleg vereist — dan stopt de planner en meldt dit, geen plan met giswerk.

---

## 3. Stap 2 — Goedkeuring (`/keur-plan-goed`)

Team leest het plan, past eventueel aan in overleg. Pas ná expliciete goedkeuring gaat de status naar `approved`. Zonder dit commando gaat de builder niet aan de slag.

---

## 4. Stap 3 — Automode-uitvoering (`/bouw-slice`)

- De `builder` voert het goedgekeurde plan uit: overzichtelijke bestanden (proactief opsplitsen, geen harde regelgrens), Engelse code met Nederlandse comments per blok.
- **Stophook:** geen vast aantal pogingen — bij twijfel over een aanpak stopt de builder direct en meldt het, in plaats van door te blijven proberen.
- Status → `in_uitvoering`.

---

## 5. Stap 4 — Visuele controle

Alleen van toepassing als deze slice een zichtbaar resultaat oplevert (zie `Design.md` — de meeste slices van dit onderdeel zijn vermoedelijk puur backend/API, dan vervalt deze stap en gaat het proces direct door naar stap 5).

---

## 6. Stap 5 — Onafhankelijke review (`/controleer-slice`)

De `reviewer` controleert, los van de builder:
- **Functionaliteit** tegen de Definition of Done uit het planbestand (`.claude/plans/<slice-id>.md`) — werkt het zoals in `Backlog.md` omschreven, niet meer/niet minder.
- **Code-conventies:** Nederlandse comments per blok aanwezig, bestandsstructuur/overzichtelijkheid, geen ongeautoriseerde nieuwe dependencies.

Gevonden problemen lost de reviewer zelf op. Status → `gereviewd`.

---

## 7. Stap 6 — Breker (`/breek-site`)

De `breker` probeert het gereviewde resultaat actief kapot te maken, met **evenveel gewicht** op:
- **API-beveiliging:** kan iemand zonder geldige API-key toch data ophalen; verkeerde bestandstypen, corrupte of te grote bestanden bij de upload-route correct afgehandeld.
- **Technische randgevallen:** lege invoer, extreem grote invoer, verkeerde/onverwachte datatypes.

Vindt de breker iets: direct zelf fixen, niet alleen rapporteren.

---

## 8. Stap 7 — Uitleg on demand (`/leg-uit`)

Op elk moment door een teamlid aan te roepen, ook niet-coders. Legt in gewone taal uit wat een slice doet, wat er gebouwd is en wat de huidige status is — direct in de chat, geen apart document.

---

## 9. Stap 8 — Afronding (`/github-afronding`)

- Opent een Pull Request op een feature branch (nooit direct naar `main`).
- PR-beschrijving: korte samenvatting van wat gebouwd is, en wat de reviewer en breker hebben gevonden/gefixt.
- Het team beoordeelt en merget zelf — de "laatste controle".
- Na merge herhaalt het proces met de volgende `/nieuwe-slice Sx`.

---

## 10. Gerelateerde documenten

| Document | Relevantie voor dit document |
|---|---|
| `CLAUDE.md` | Stophooks, procesoverzicht, git-flow |
| `Architecture.md` | Techniek — basis voor de breker's technische testen |
| `Backlog.md` | Input voor de planner bij elke `/nieuwe-slice` |
