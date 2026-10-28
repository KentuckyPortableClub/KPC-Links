# US-AZ official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| nps.gov | 19 | 19 | `nps.gov/grca/planyourvisit/upload/<file.pdf>` | US-0030 Grand Canyon National Park: https://www.nps.gov/grca/planyourvisit/upload/GRCAmap2.pdf → ok; date not stated<br>US-0057 Petrified Forest National Pa: https://www.nps.gov/pefo/planyourvisit/maps.htm → ok; date not stated<br>US-0060 Saguaro National Park: https://www.nps.gov/sagu/planyourvisit/maps.htm → ok; date Page last updated May 29, 2025; individual map dates not sta |
| azgfd.com | 9 | 0 | `azgfd.com/wildlife/viewing/wheretogo/robbins/<page>` | US-11028 Robbins Butte Wildlife Area : https://www.azgfd.com/wildlife/viewing/wheretogo/robbins/ → HTTP 403; date not stated<br>US-11087 Upper Verde River State Wild: https://www.azgfd.com/wildlife/viewing/wheretogo/upperverde/ → HTTP 403; date not stated<br>US-11946 Willcox Playa State Wildlife: https://www.azgfd.com/wildlife/viewing/wheretogo/wilcoxplaya/ → HTTP 403; date not stated |
| fs.usda.gov | 5 | 5 | `fs.usda.gov/r03/apache-sitgreaves/<page>` | US-4427 Apache-Sitgreaves National F: https://www.fs.usda.gov/r03/apache-sitgreaves/maps-guides → ok; date not stated<br>US-4428 Coconino National Forest: https://www.fs.usda.gov/sites/nfs/files/r03/coconino/publication/2025-travel-map.pdf → ok; date April 15, 2025<br>US-4429 Coronado National Forest: https://www.fs.usda.gov/r03/coronado/maps-guides → ok; date not stated |
| blm.gov | 3 | 3 | `blm.gov/sites/blm.gov/files/docs/2020-12/<file.pdf>` | US-4436 Vermilion Cliffs National Mo: https://www.blm.gov/sites/blm.gov/files/docs/2020-12/AZ_VermilionCliffs_NM_map-508.pdf → ok; date not stated<br>US-7381 Las Cienegas National Conser: https://www.blm.gov/documents/arizona/public-room/map/las-cienegas-national-conservation-area → ok; date not stated<br>US-8312 Gila Box Riparian National C: https://www.blm.gov/documents/arizona/public-room/map/gila-box-riparian-national-conservation-area → ok; date not stated |
| home.nps.gov | 1 | 1 | `home.nps.gov/lake/planyourvisit/<file.htm>` | US-0676 Lake Mead National Recreatio: https://home.nps.gov/lake/planyourvisit/maps.htm → ok; date Page last updated May 28, 2026 |
| azstateparks.com | 1 | 0 | `azstateparks.com/catalina/explore/<page>` | US-1055 Catalina State Park: https://azstateparks.com/catalina/explore/maps → HTTP 403; date not stated |

**Totals:** 38 park map links, 28 bot-ok (74%).

## BOT LOOK-UP (script-loaded or failed links)
- azgfd.com: 9 of 9 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- azstateparks.com: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency

## Desk research Oct 28 (thin)
- Bot data: Arizona Game and Fish (azgfd.com) 0 of 9 links open (A): BOT LOOK-UP the AZGFD area pages. NPS 19 of 19, Forest Service 5 of 5, BLM 3 of 3 open. Arizona State Parks (azstateparks.com): no bot-checked link; search returned only map shops, so the pattern is NOT FOUND this pass: BOT LOOK-UP. Handovers: none seen.
