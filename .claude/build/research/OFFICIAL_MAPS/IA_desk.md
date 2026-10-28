# US-IA official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| iowadnr.gov | 4 | 3 | `iowadnr.gov/places-go/<page>` | US-12376 Blackburn Wildlife Managemen: https://www.iowadnr.gov/places-go/wildlife-management-areas → ok; date not stated<br>US-2281 Big Creek State Park: https://www.iowadnr.gov/portals/idnr/uploads/parks/parkmaps/bigcreekmap.pdf → HTTP 404; date Map date not stated<br>US-4655 Backbone State Forest: https://www.iowadnr.gov/places-go/state-forests/backbone-state-forest → ok; date not stated |
| nps.gov | 2 | 2 | `nps.gov/heho/planyourvisit/<file.htm>` | US-0832 Herbert Hoover National Hist: https://www.nps.gov/heho/planyourvisit/maps.htm → ok; date not stated<br>US-0922 Effigy Mounds National Monum: https://www.nps.gov/efmo/planyourvisit/maps.htm → ok; date not stated |

**Totals:** 6 park map links, 5 bot-ok (83%).

## BOT LOOK-UP (script-loaded or failed links)
- iowadnr.gov: 1 of 4 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency

## Desk research Oct 28
- **Iowa DNR:** WMA listing is a dashboard (https://www.arcgis.com/apps/dashboards/b8a7ff4dc22343fdb1177db6df794676) and a Hunting Atlas viewer (iowadnr.maps.arcgis.com webappviewer); the page has no park maps (A). Page patterns: `iowadnr.gov/places-go/wildlife-management-areas/<slug>`, `.../places-go/state-parks/all-parks/<slug>` (A). Map files not found in text: BOT LOOK-UP, read each park page's map link. Open GIS: https://programs.iowadnr.gov/geospatial/rest/services/Recreation/State_Parks/MapServer (B) - to chat 9.
- **Rules:** WMA rules = Iowa Administrative Code Chapter 51 (legis.iowa.gov/DOCS/ACO/IAC/LINC/Chapter.571.51.pdf), refuges Chapter 52, parks https://www.iowadnr.gov/places-go/state-parks/parks-use-rules-guidelines (A). Dates: page updated 2026-09-18; no map dates.
- Handovers: none seen.
