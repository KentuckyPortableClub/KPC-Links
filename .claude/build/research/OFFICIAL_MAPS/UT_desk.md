# US-UT official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| nps.gov | 16 | 16 | `nps.gov/arch/planyourvisit/<file.htm>` | US-0004 Arches National Park: https://www.nps.gov/arch/planyourvisit/maps.htm → ok; date not stated<br>US-0009 Bryce Canyon National Park: https://www.nps.gov/brca/planyourvisit/maps.htm → ok; date not stated<br>US-0010 Canyonlands National Park: https://www.nps.gov/cany/planyourvisit/maps.htm → ok; date not stated |
| blm.gov | 8 | 6 | `blm.gov/sites/blm.gov/files/<file.pdf>` | US-11112 Factory Butte BLM Recreation: https://www.blm.gov/sites/blm.gov/files/BLMUtahFactoryButteMap.pdf → ok; date not stated<br>US-5750 Black Ridge Canyons Wilderne: https://www.blm.gov/programs/national-conservation-lands/colorado/black-ridge-canyons-wilderness → HTTP 404; date not stated<br>US-5768 Bonanza BLM Herd Management : https://www.blm.gov/programs/wild-horse-and-burro/herd-management → ok; date not stated |
| stateparks.utah.gov | 4 | 1 | `stateparks.utah.gov/parks/deer-creek/map/<page>` | US-3067 Deer Creek State Park: https://stateparks.utah.gov/parks/deer-creek/map/ → HTTP 404; date not stated<br>US-3091 Snow Canyon State Park: https://stateparks.utah.gov/wp-content/uploads/sites/13/2023/02/web-Snow-Canyon-Trail-Guide-Map-Brochure-2023.pdf → HTTP 404; date not stated<br>US-5913 Historic Union Pacific Rail : https://stateparks.utah.gov/parks/historic-union-pacific-rail-trail/map/ → HTTP 404; date not stated |
| fs.usda.gov | 3 | 3 | `fs.usda.gov/r04/dixie/planning/forest-plan/<page>` | US-4395 Dixie National Forest: https://www.fs.usda.gov/r04/dixie/planning/forest-plan/forest-plan-and-amendments → ok; date Forest plan map dates not stated on page<br>US-4398 Uinta-Wasatch-Cache National: https://www.fs.usda.gov/r04/uinta-wasatch-cache/maps-guides → ok; date not stated<br>US-5793 Flaming Gorge National Recre: https://www.fs.usda.gov/sites/nfs/files/r04/ashley/publication/Ashley%20Visitor%20Guide.pdf → ok; date not stated |
| grandcountyutah.net | 1 | 0 | `grandcountyutah.net/Facilities/Facility/Details/<page>` | US-5790 Sand Flats State Recreation : https://www.grandcountyutah.net/Facilities/Facility/Details/Sand-Flats-Recreation-Area-1 → HTTP 404; date not stated |
| wildlife.utah.gov | 1 | 0 | `wildlife.utah.gov/hunting/hunting-in-utah/<file.html>` | US-5923 Henefer-Echo UDWR Wildlife M: https://wildlife.utah.gov/hunting/hunting-in-utah/wildlife-management-areas.html → HTTP 404; date not stated |

**Totals:** 33 park map links, 26 bot-ok (79%).

## BOT LOOK-UP (script-loaded or failed links)
- blm.gov: 2 of 8 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- stateparks.utah.gov: 3 of 4 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- grandcountyutah.net: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- wildlife.utah.gov: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency

## Desk research Oct 28
- **Utah DWR WMAs:** one ArcGIS Experience viewer (experience.arcgis.com/experience/2cb690e760b444e7a280af164e6f6766/) with a per-WMA layer index in the link (Topaz and Timpie Springs share index 231: one is wrong) (A). No per-WMA files, no map dates (page 'Last updated Aug 27 2026'). GIS hub: https://dwr-data-utahdnr.hub.arcgis.com/ (A) - to chat 9. Hunt boundaries: hunt.utah.gov, dwrapps.utah.gov/huntboundary/hbstart (A).
- **Utah State Parks:** old pattern `site.utah.gov/stateparks/wp-content/uploads/sites/13/<YYYY>/<MM>/<Park>-Map.pdf` (B, Utah-Lake-State-Park-SE-Map.pdf, 2018/01 = a date clue); bot ok only 1 of 4 on stateparks.utah.gov: BOT LOOK-UP. BLM Utah 6 of 8 ok. Handovers: none seen (Utah Lake state park was an earlier NOT SURE, see the verdict file).
