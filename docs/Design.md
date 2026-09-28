# DESIGN.md
### QUEST — Onderdeel 4 — Automatiseren bouwtekeningen

> **Status:** v0.1 — concept, opgesteld in overleg met Alex van Bommel.
> **Datum:** 25 september 2026

---

## 1. Zichtbare interface: nee

Dit onderdeel is **puur een API-service**, zonder eigen zichtbare interface voor eindgebruikers. Alle presentatie aan de VvE-gebruiker gebeurt in onderdeel 5's dashboard/rapport (zie `Onderdeel5_Interfaces_voorstel.md` §6). Onderdeel 4 levert enkel een tekening-referentie, gebruikte route en status terug via de API (`Interfaces.md` §2).

**Gevolg voor `Workflow.md` §5:** de stap "Visuele controle" vervalt in de praktijk voor vrijwel alle slices van dit onderdeel, aangezien er niets visueels op te leveren valt. Het proces gaat na `/bouw-slice` direct door naar `/controleer-slice`.

---

## 2. Mocht dit ooit wijzigen

Als er tijdens de spike-week of later toch behoefte blijkt aan bijvoorbeeld een interne testpagina (om job-statussen te bekijken, een geconverteerde tekening te previewen, of een handmatige route-b-upload te testen zonder de API rechtstreeks aan te roepen), dan geldt:

- Basis: de Inside Out-merkkleuren uit `Huisstijl_en_conventies.md` §1 (`#004238` groen, `#CCFF00` lime), spaarzaam als accent — niet als grote vlakken.
- Toegankelijkheid en motion: zie `Huisstijl_en_conventies.md` §3–4, aan te raden zodra er een interface bijkomt.
- Zo'n testpagina is dan een **eigen, aparte slice** in `Backlog.md` (nooit stilzwijgend meegebouwd binnen een API-slice), zodat expliciet zichtbaar blijft dat dit een bewuste toevoeging is en geen onderdeel van de kernscope.

---

## 3. Gerelateerde documenten

| Document | Relevantie voor dit document |
|---|---|
| `CLAUDE.md` | §4 — huisstijlconventies, alleen relevant bij §2 hierboven |
| `Onderdeel5_Interfaces_voorstel.md` | §6 — waar de eindgebruiker de resultaten van dit onderdeel wél te zien krijgt |
| `Workflow.md` | §5 — visuele-controle-stap, in de praktijk overgeslagen voor dit onderdeel |
| `Backlog.md` | Een eventuele testpagina (§2) wordt daar als losse, expliciete slice opgenomen, niet aangenomen |
