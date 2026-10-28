# US-TN official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| nps.gov | 7 | 7 | `nps.gov/cuga/planyourvisit/<file.htm>` | US-0019 Cumberland Gap National Hist: https://www.nps.gov/cuga/planyourvisit/maps.htm → ok; date not stated<br>US-0034 Great Smoky Mountains Nation: https://www.nps.gov/grsm/planyourvisit/maps.htm → ok; date not stated<br>US-0685 Obed National Wild and Sceni: https://www.nps.gov/obed/planyourvisit/maps.htm → ok; date not stated |
| lrn.usace.army.mil | 2 | 0 | `lrn.usace.army.mil/Locations/Lakes/CordellHullLake/<file.aspx>` | US-7580 Cordell Hull Wildlife Manage: http://www.lrn.usace.army.mil/Locations/Lakes/CordellHullLake/Maps.aspx → HTTP 400; date not stated<br>US-7610 Old Hickory Wildlife Managem: http://www.lrn.usace.army.mil/Locations/Lakes/OldHickoryLake/Maps.aspx → HTTP 400; date not stated |
| tnstateparks.com | 1 | 0 | `tnstateparks.com/sites/default/files/2025-09/<file.pdf>` | US-2982 Warriors' Path State Park: https://tnstateparks.com/sites/default/files/2025-09/warriors_path_brochure.pdf → HTTP 403; date not stated |
| landbetweenthelakes.us | 1 | 1 | `landbetweenthelakes.us/help-center/lbl-maps/<page>` | US-3792 Land Between the Lakes Natio: https://www.landbetweenthelakes.us/help-center/lbl-maps/ → ok; date 2026 MVUM; recreation maps include 2022 editions |
| fs.usda.gov | 1 | 1 | `fs.usda.gov/cherokee/<page>` | US-4525 Cherokee National Forest: https://www.fs.usda.gov/cherokee/maps-pubs → ok; date Map date varies by map; not stated on landing page |
| trails.nc.gov | 1 | 1 | `trails.nc.gov/maps/map-pdfs-mountains-sea-state-trail/<page>` | US-8313 Mountains to Sea State Trail: https://trails.nc.gov/maps/map-pdfs-mountains-sea-state-trail/open → ok; date not stated |

**Totals:** 13 park map links, 10 bot-ok (77%).

## BOT LOOK-UP (script-loaded or failed links)
- lrn.usace.army.mil: 2 of 2 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- tnstateparks.com: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency

## Desk research Oct 28
- **Wildlife areas (TWRA):** list page https://www.tn.gov/twra/gis-maps/wildlife-management-area--wma--maps.html (an interactive map plus a few download links; file addresses not shown, no dates, A). Region pages: tn.gov/twra/wildlife-management-areas/{west-tennessee-r1, middle-tennessee-r2, cumberland-plateau-r3, east-tennessee-r4}.html (B). The list page does not link a rules page; it says users must know the land owner's rules (A).
- **State parks (tnstateparks.com):** pattern `tnstateparks.com/sites/default/files/<YYYY-MM>/<park>_brochure.pdf` (the folder is the upload month, a rough map date; bot got 403): BOT LOOK-UP.
- **State layer for outlines:** https://tnmap.tn.gov/arcgis/rest/services/ENVIRONMENTAL/PUBLIC_LANDS/MapServer (B).
- Corps (lrn.usace.army.mil .../Maps.aspx): both links 400: BOT LOOK-UP. Land Between the Lakes: landbetweenthelakes.us/help-center/lbl-maps/ ok (A, bot).
- Handovers: none seen.
