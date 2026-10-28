# US-CO official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| nps.gov | 13 | 13 | `nps.gov/blca/planyourvisit/<file.htm>` | US-0008 Black Canyon of the Gunnison: https://www.nps.gov/blca/planyourvisit/maps.htm → ok; date not stated<br>US-0033 Great Sand Dunes National Pa: https://www.nps.gov/grsa/planyourvisit/maps.htm → ok; date not stated<br>US-0051 Mesa Verde National Park: https://www.nps.gov/meve/planyourvisit/maps.htm → ok; date not stated |
| cpw.state.co.us | 10 | 10 | `cpw.state.co.us/sites/default/files/dam/vhuuk6xtqt/<file.pdf>` | US-0184 Ramah State Wildlife Area: https://cpw.state.co.us/sites/default/files/dam/vhuuk6xtqt/ramahswa_geo.pdf → ok; date not stated<br>US-1209 Barr Lake State Park: https://cpw.state.co.us/sites/default/files/dam/typuvxypbr/barr-lake-state-park-brochure.pdf → ok; date not stated<br>US-1210 Boyd Lake State Park: https://cpw.state.co.us/state-parks/boyd-lake-state-park → ok; date not stated |
| fs.usda.gov | 4 | 4 | `fs.usda.gov/r02/gmug/<page>` | US-4402 Gunnison National Forest: https://www.fs.usda.gov/r02/gmug/maps-guides → ok; date not stated<br>US-4404 Pike National Forest: https://www.fs.usda.gov/r02/psicc/maps-guides → ok; date not stated<br>US-4407 San Isabel National Forest: https://www.fs.usda.gov/psicc/maps-pubs → ok; date Map date varies by map; not stated on landing page |
| fws.gov | 2 | 2 | `fws.gov/sites/default/files/documents/2024-06/<file.pdf>` | US-0225 Rocky Flats National Wildlif: https://fws.gov/sites/default/files/documents/2024-06/rocky-flats-nwr-brochure-web.pdf → ok; date 2024-06<br>US-0226 Rocky Mountain Arsenal Natio: https://www.fws.gov/sites/default/files/documents/2025-03/rma-wildlife-drive-and-trails-web.pdf → ok; date January 2025 |
| blm.gov | 1 | 0 | `blm.gov/visit/<page>` | US-9596 North Sand Hills BLM Nationa: https://www.blm.gov/visit/north-sand-hills-recreation-area → HTTP 404; date not stated |

**Totals:** 30 park map links, 29 bot-ok (97%).

## BOT LOOK-UP (script-loaded or failed links)
- blm.gov: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency
