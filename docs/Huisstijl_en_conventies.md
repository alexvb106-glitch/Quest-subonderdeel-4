# HUISSTIJL-EN-CONVENTIES.md
### QUEST — gedeeld tussen alle onderdelen

> Dit document kun je ongewijzigd in de `docs/`-map van élk QUEST-onderdeel zetten. Het bevat alleen wat écht projectbreed vaststaat of aan te raden is voor consistentie — niet de techniek, het datamodel of de specifieke UI, want die verschillen per onderdeel.

---

## 1. Merkkleuren (Inside Out) — bevestigd, hard

Rechtstreeks uit het Inside Out-logo (inside-out.tech), dus dit geldt overal waar het merk zichtbaar is:

| Rol | Kleur | Hex |
|---|---|---|
| Primair / merkaccent | Inside Out Groen | `#004238` |
| Highlight / attention | Inside Out Lime | `#CCFF00` |

Gebruik: spaarzaam als accent op een wit/grijze basis — niet als grote vlakken. Lime nooit als tekstkleur op een lichte achtergrond (te laag contrast); alleen als kleine achtergrond/stip met donkere tekst erop.

`[LET OP]` Dit zijn de enige twee kleuren die daadwerkelijk uit het echte logo komen. Een volledig kleurenschema (achtergrond, tekst, randen, dark mode) is voor onderdeel 5 zelf ingevuld — als jouw onderdeel een eigen interface krijgt, opnieuw opbouwen op basis van deze twee merkkleuren, niet de rest van onderdeel 5's schema blind overnemen.

---

## 2. Typografie — aanbevolen, niet bevestigd door Inside Out

Voor onderdeel 5 gekozen: **IBM Plex Sans** (UI-tekst) en **IBM Plex Mono** (technische/data-labels). Dit is een eigen ontwerpkeuze, geen vastgesteld Inside Out-lettertype — gebruik het voor consistentie als je onderdeel een eigen interface heeft, maar het is geen harde eis.

---

## 3. Toegankelijkheid — aan te raden voor elk onderdeel met een interface

Voldoende contrast (WCAG AA minimaal), leesbare tekstgroottes, duidelijke focus-states voor toetsenbordnavigatie, geen informatie die uitsluitend via kleur wordt overgebracht.

---

## 4. Motion — aan te raden

Spaarzaam en doelgericht: motion alleen als reactie op een actie van de gebruiker, niet als decoratie.

---

## 5. Taal- en code-conventies — aanbevolen voor consistentie, geen verplichting

Voor onderdeel 5 gekozen, en aan te raden als teambrede afspraak zodat de hele QUEST-codebase leesbaar blijft voor elkaar:
- **Code** (variabelen, functienamen, bestandsnamen): Engels.
- **Code-comments:** Nederlands, per logisch codeblok.
- **UI-teksten richting eindgebruikers:** Nederlands.
- **Documentatie:** Nederlands.

Ieder team kan hiervan afwijken als daar een goede reden voor is — dit is geen technisch afgedwongen regel.

---

## 6. Open vraag: geldt "productieniveau" voor alle onderdelen?

Onderdeel 5 is bewust op **echt productieniveau** gebouwd (`claude.md` §3) — het moederbedrijf brengt de tool aan het einde van dit half jaar naar de markt. Of dezelfde eis geldt voor onderdeel 1–4 (bijv. moet de dakoppervlaktestudie ook productierijp zijn, of mag die backend-matig op een lager afwerkingsniveau blijven zolang hij werkt?) is **niet vastgesteld** — dat is een keuze die per onderdeel, of centraal voor het hele project, nog gemaakt moet worden. Aan te raden om dit met alle vijf de teams af te stemmen, niet aan te nemen.
