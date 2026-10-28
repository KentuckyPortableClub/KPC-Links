# US-ME official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| nps.gov | 4 | 4 | `nps.gov/acad/planyourvisit/<file.htm>` | US-0001 Acadia National Park: https://www.nps.gov/acad/planyourvisit/maps.htm → ok; date Map date not stated<br>US-10713 Katahdin Woods and Waters Na: https://www.nps.gov/kaww/planyourvisit/maps.htm → ok; date not stated<br>US-11808 Saint Croix Island Internati: https://www.nps.gov/sacr/planyourvisit/maps.htm → ok; date not stated |

**Totals:** 4 park map links, 4 bot-ok (100%).

## BOT LOOK-UP (script-loaded or failed links)
- none from this pass

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency

## Desk research Oct 28
- **Maine Bureau of Parks and Lands (DACF):** list https://www.maine.gov/dacf/parks/publications_maps/index.shtml (A). Brochures `maine.gov/dacf/parksearch/PropertyGuides/PDF_GUIDE/<name>.pdf`; full-size maps `.../PropertyGuides/Maps/FullSize/<name>.pdf` (A). No years in names; page footer 'Copyright 2021' only (A): map dates unknown, treat as old. Conservation lands overview: .../conservation_lands_maine.html (B). Bot data: only NPS links, so no Maine agency link was ever checked: BOT LOOK-UP the patterns above. Handovers: none seen.
