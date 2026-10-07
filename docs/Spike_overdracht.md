# Onderdeel 4 — Overdracht na spike-week (S0.2)

Opgesteld op 7 oktober 2026. Doel: startpunt voor het werken aan de slices. Sluit slice S0.2 uit `Backlog.md` af.
De volledige stukken staan lokaal bij Alex in de map `spike alex`: `SAMENVATTING.md`, `VERGELIJKING_alex-jeroen.md`, `LOGBOEK.md`, `INVENTARIS.md` en de mappen `poging1`, `poging2`, `poging3`. Jeroens stukken staan in `overdracht-jeroen`.

## Scopebesluit voor nu

**De constructieve parameters blijven voorlopig buiten de slices:** dragende wanden, ketelhuis of technische ruimte, en draagvermogen van het dak.
Reden: Alex vraagt bij Inside Out (Olivier) na of de tool dit moet behandelen, of dat het bij de VvE of een externe constructieadviseur blijft. Tot dat antwoord er is: niet bouwen, niet ontwerpen, alleen ruimte laten in het uitvoerformaat.

## Wat de spike opleverde

| | Alex | Jeroen |
|---|---|---|
| Invoer | Kleurenscan uit 1964, dakaanzicht hoogbouw Theemsdreef (Utrecht), schaal 1:100 | Vector-PDF uit Revit, woongebouw Naxosdreef (Utrecht), schaal 1:100 |
| Techniek | Python (spike gedraaid op 3.14.3), OpenCV: lijnen en vormen in het beeld. Geen OCR; maten overgetypt. | Python 3.14.7, PyMuPDF: tekst met positie uit de PDF, maatketens optellen |
| Resultaat | Dakomtrek 109,13 × 12,71 m, 6 dakopbouwen, kleine obstakels onbetrouwbaar | Breedte 25370 mm, diepte 9860 mm, peilen, verdiepingshoogte 2800 mm |
| Nauwkeurigheid | Lengte −0,4%, breedte +0,4% na aparte ijking (anders −3,1%) | 0% op schaal, breedte en diepte; rest niet gecontroleerd |
| Handwerk | Veel, vooraf: zoekvensters, maten overtypen, eindpunten aanwijzen | Weinig, achteraf: twijfelgevallen nakijken |
| Uitvoer | JSON, DXF, HTML-rapport met betrouwbaarheid per waarde | Tekstbestanden plus bewijsbestand per uitkomst |

**Gezamenlijke test (poging 3):** de dakranddetectie van Alex op Jeroens tekening gaf een diepte van 9869 mm tegen 9860 mm (+0,09%). De techniek is overdraagbaar; de instellingen (zeven zoekvensters, vier drempels) moesten opnieuw met de hand.

## Bevindingen die de slices sturen

1. **Maten uit getallen, vorm uit lijnen.** Een geschreven maat is betrouwbaarder dan een gemeten lijn.
2. **Een oude scan is niet maatvast:** 3,6% verschil tussen lengte en breedte. Op een digitale tekening is dat verschil er niet.
3. **De tekening vinden is moeilijker dan lezen.** Zoeken op straatnaam gaf ongemerkt een ander pand (Adriaen van Ostadelaan: nr. 140 in plaats van nr. 155). Jeroens archiefscans uit Amersfoort waren onleesbaar. Het adres in het titelblok is leidend.
4. **Controle moet in het ontwerp zitten en los staan van de detectie.** Jeroens optelsom en Alex' tweede maat zijn hetzelfde idee.
5. **De AI liet in de spike van Alex drie keer een controle slagen die niet was uitgevoerd.** De reviewer en breker moeten hier gericht op letten.
6. **Geen van beiden gebruikte een externe bron.** 3DBAG is de logische onafhankelijke controle en het vangnet.
7. **Niet getest door wie dan ook:** OCR op handgeschreven maatcijfers, en een tweede tekening per route.
8. **Open ontwerpvraag:** hoe vindt de tool zelf het juiste deel van een blad?

## Voorstel voor de opbouw (nog te bevestigen door Alex en Jeroen)

- Eén ingang die bepaalt of een bestand vector of scan is.
- Eén tussenformaat per getal: waarde, positie, richting, bron en betrouwbaarheid.
- Jeroens optelsom draait op dat tussenformaat, voor beide routes.
- Alex' vormdetectie vult aan met dakomtrek en obstakels.
- Eén set labels: bewezen, onzeker, ontbreekt.
- Uitvoer: JSON voor onderdeel 5, DXF voor geometrie, een leesbaar rapport, en een bewijsbestand.

## Voorgestelde volgorde van de slices

1. S0.1 Repo en scaffolding
2. S0.3 API-skeleton met authenticatie
3. Nieuw: tussenformaat en betrouwbaarheidslabels
4. S1.x Route (c), vector-PDF
5. S1.x Route (c), scan
6. S0.4 Job-queue (keuze stond op "na S0.2")
7. S2.1 en S2.2 Mocks voor onderdeel 1 en 5
8. S1.y Route (a) als haalbaarheidsslice; de uitkomst mag negatief zijn

## Nog te doen voor de eerste slice

- [ ] S0.2 afsluiten in de backlog en Fase 1 invullen
- [ ] Samenvoegbesluit met Jeroen vastleggen
- [ ] PvA deelproduct 4 aanpassen: de aanname van recente tekeningen klopt niet meer
- [x] Eén Python-versie: beiden werken sinds 7 oktober 2026 met Python 3.14.7
- [ ] Antwoord van Olivier over de constructie vastleggen zodra het er is

Spike-code is wegwerpcode: de inzichten gaan mee naar de repo, de scripts niet.
