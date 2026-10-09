# CLAUDE.md
### QUEST — Onderdeel 4 — Automatiseren bouwtekeningen

> **Status:** v0.1 — concept, opgesteld in overleg met Alex van Bommel (rol: Beheren) en Jeroen van Leening (rol: Realiseren).
> **Datum:** 25 september 2026
> **Team:** Alex van Bommel, Jeroen van Leening — beiden Built Environment (BE).

---

## 1. Doel van dit onderdeel

Het gezochte gebouw koppelen aan een bruikbare bouwtekening, zodat onderdeel 5 kan tonen of en hoe **io Alpha** (dakconstructie) en **io Bravo** (klimaathub) op het gebouw passen (zie `scope en url inside out - alpha en bravo module`).

`[SCOPE-WIJZIGING t.o.v. de oorspronkelijke kickoff, 25-09-2026]` De oorspronkelijke drie routes gingen uit van Revit als centraal formaat. Na verkenning door het team vervalt Revit als primaire route: **Revit-tekeningen zijn niet publiek toegankelijk, en de meeste VvE's hebben zelf ook geen Revit-model.** Dit is teruggekoppeld naar onderdeel 5 (zie `Onderdeel5_Interfaces_voorstel.md`, statusnotitie onderaan) omdat het rechtstreeks hun voorgestelde contract raakt.

### Herziene routes

| Route | Omschrijving | Status |
|---|---|---|
| **(a) Archiefonderzoek + conversie** | Automatisch zoeken in een (gemeentelijk) bouwarchief, resulterend in een neutraal tussenformaat (bijv. IFC/DXF) i.p.v. een gescript Revit-model. | Primair, nog te onderzoeken welk archief geautomatiseerd doorzoekbaar is. |
| **(b) Bestaand Revit-bestand** | Alleen relevant als een specifieke VvE toevallig zelf een Revit-model heeft. | **Secundair — stub/opzet.** Niet de aanname, wel een voorbereide (niet-uitgewerkte) ingang voor het geval dit voorkomt. |
| **(c) Archief-PDF + conversiescript** | Handmatig invoegen van een gevonden archief-PDF, geautomatiseerd omgezet naar een bruikbare tekening. | Primair, samen met (a). |

`[OPEN]` Exact uitvoerformaat van (a) en (c) — richting IFC/DXF, in afwachting van verdere verkenning. Vastleggen in `Architecture.md`.

---

## 2. Herbruikbare assets

Er bestaan al werkende Dynamo-scripts voor de automatische plaatsing van io Alpha en io Bravo op een Revit-project (referentieprojecten aanwezig). Dit is waardevol als referentie voor plaatsings-/conversielogica, ook nu Revit niet meer de primaire route is — nader te bepalen in `Architecture.md` hoe/of dit hergebruikt wordt.

Bouwtekeningen zelf worden **niet** door Inside Out aangeleverd; het team vraagt deze zelf op bij de gekozen archiefbron(nen).

---

## 3. Werkwijze — eerste week

Voordat de architectuur definitief vastligt: Alex en Jeroen verkennen **individueel, ieder een week**, hoe ver ze zelfstandig komen met een eigen proof-of-principle voor hun deel. Na die week wordt bepaald of de twee aanpakken samengevoegd worden of dat er gezamenlijk opnieuw wordt gestart op basis van wat werkte.

`[LET OP voor Backlog.md]` Dit betekent dat Fase 0 een verkennings-/spike-slice per persoon nodig heeft, vóór de gebruikelijke "repo & scaffolding"-slice die voor beide geldt.

---

## 4. Taal- en huisstijlconventies

Zie `Huisstijl_en_conventies.md` (projectbreed, ongewijzigd overnemen):
- Code in het Engels, comments in het Nederlands per logisch blok, documentatie en eindgebruikersteksten in het Nederlands.
- Inside Out-merkkleuren (`#004238` groen, `#CCFF00` lime) alleen relevant als dit onderdeel ooit een zichtbare interface krijgt — dat is nog niet vastgesteld, zie `Design.md`.

---

## 5. Slice-principe en stophook-filosofie

Werk in kleine, afgebakende slices (zie `Workflow.md` voor het volledige draaiboek). Geen vast aantal pogingen bij een probleem: bij twijfel over een technische aanpak, een architectuurkeuze, of iets dat niet expliciet in `Backlog.md` staat, stopt de betreffende subagent direct en meldt dit — in plaats van zelf door te blijven proberen of te gokken.

---

## 6. Bestandsstructuur

Geen harde regelgrens per bestand. Overzichtelijkheid is leidend: proactief opsplitsen in kleinere, logisch gescheiden bestanden zodra een bestand moeilijk overzichtelijk wordt.

---

## 7. Git-afspraak

- Eén feature branch per slice, nooit rechtstreeks naar `main`.
- Pull Request per slice; het team (Alex en Jeroen) beoordeelt deze zelf, per persoon (roulerend, geen vaste reviewer).
- Repository: nog niet aangemaakt — wordt per subteam (dus ook door onderdeel 4 zelf) opgezet, niet centraal door Kai.

---

## 8. Afwerkingsniveau

`[VOORLOPIG — nog niet teambreed bevestigd]` Voorkeur van dit team: **niveau B — proof-of-concept-niveau.** Werkend en demonstreerbaar genoeg om te koppelen aan onderdeel 5, niet per se productierijp zoals onderdeel 5 zelf. Dit is al bij het team geagendeerd; de definitieve, teambrede bevestiging (zie `Huisstijl_en_conventies.md` §6) staat nog open. Tot bevestiging bouwt dit onderdeel op basis van niveau B.

---

## 9. Open punten richting onderdeel 5

- `[OPEN]` Of route (b) (bestaand Revit-bestand, nu uitzondering i.p.v. hoofdroute) via een upload in onderdeel 5's eigen interface loopt, of via onderdeel 4's eigen API — nog te bespreken met het team van onderdeel 5.
- Contract uit `Onderdeel5_Interfaces_voorstel.md` §5 (input: building-referentie/adres; output: tekening-referentie, gebruikte route, status) is inhoudelijk akkoord vanuit onderdeel 4. Wel aan te passen zodra de Revit-scope-wijziging is doorgesproken met onderdeel 5.

---

## 10. Testcase

Nog geen VvE-pand definitief geselecteerd — werving loopt. Selectiecriteria: bereidheid tot medewerking van de VvE, én voldoende beschikbare archiefdata. Bekend: bij veel gemeenten is doorgaans voldoende archiefmateriaal te vinden, wat dit als haalbare route ondersteunt.

---

## 11. Gerelateerde documenten

| Document | Status |
|---|---|
| `CLAUDE.md` | Dit document (v0.1) |
| `Architecture.md` | ✅ v0.6 |
| `Interfaces.md` | ✅ v0.1 |
| `Design.md` | ✅ v0.1 |
| `Workflow.md` | ✅ Klaar |
| `Backlog.md` | ✅ v0.3 |
| `Huisstijl_en_conventies.md` | ✅ Projectbreed, ongewijzigd |
| `Onderdeel5_Interfaces_voorstel.md` | ✅ Referentie, met scope-statusnotitie |
