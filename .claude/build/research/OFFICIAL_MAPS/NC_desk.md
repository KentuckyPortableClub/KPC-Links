# US-NC official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| ncparks.gov | 37 | 36 | `ncparks.gov/maps/carolina-beach-state-park-map/<page>` | US-2722 Carolina Beach State Park: https://www.ncparks.gov/maps/carolina-beach-state-park-map/open → ok; date not stated<br>US-2723 Carvers Creek State Park: https://www.ncparks.gov/state-parks/carvers-creek-state-park/plan-your-visit → ok; date Map dates not stated<br>US-2725 Cliffs of the Neuse State Pa: https://www.ncparks.gov/maps/cliffs-neuse-state-park-map/open → ok; date not stated |
| nps.gov | 6 | 6 | `nps.gov/caha/planyourvisit/<file.htm>` | US-0682 Cape Hatteras National Seash: https://www.nps.gov/caha/planyourvisit/maps.htm → ok; date ORV access map 2025; page updated July 29, 2025<br>US-0683 Cape Lookout National Seasho: https://www.nps.gov/calo/planyourvisit/maps.htm → ok; date not stated<br>US-0706 Moores Creek National Battle: https://www.nps.gov/mocr/planyourvisit/maps.htm → ok; date not stated |
| ncwildlife.gov | 2 | 1 | `ncwildlife.gov/hunting/where-hunt-shoot/game-lands-maps/<page>` | US-6927 Nantahala State Game Land: https://www.ncwildlife.gov/hunting/where-hunt-shoot/game-lands-maps/mountain-game-land-maps → ok; date not stated<br>US-6958 Thurmond Chatham State Game : https://www.ncwildlife.gov/hunting/where-hunt-and-shoot/game-lands → HTTP 404; date not stated |
| trails.nc.gov | 1 | 1 | `trails.nc.gov/maps/map-pdfs-yadkin-river-state-trail/<page>` | US-12320 Yadkin River State Trail: https://trails.nc.gov/maps/map-pdfs-yadkin-river-state-trail/open → ok; date not stated |
| fs.usda.gov | 1 | 0 | `fs.usda.gov/sites/nfs/files/r08/northcarolina/publication/<file.pdf>` | US-4511 Uwharrie National Forest: https://www.fs.usda.gov/sites/nfs/files/r08/northcarolina/publication/UWH%20--%20Uwharrie%20National%20Forest%20Recreation%20Guide.pdf → HTTP 429; date Map date not stated |
| ncagr.gov | 1 | 1 | `ncagr.gov/divisions/nc-forest-service/NCFS%20-%20Mountain%20Island%20Trail%20Map.pdf/<page>` | US-4858 Mountain Island Educational : https://www.ncagr.gov/divisions/nc-forest-service/NCFS%20-%20Mountain%20Island%20Trail%20Map.pdf/open → ok; date Map date not stated |

**Totals:** 48 park map links, 45 bot-ok (94%).

## BOT LOOK-UP (script-loaded or failed links)
- ncparks.gov: 1 of 37 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- ncwildlife.gov: 1 of 2 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- fs.usda.gov: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency

## Desk research Oct 28
- **Game lands (NC Wildlife Resources Commission):** three list pages https://www.ncwildlife.gov/hunting/where-hunt-shoot/game-lands-maps/{mountain,piedmont,coastal}-game-land-maps (A for mountain). File pattern `https://www.ncwildlife.gov/media/<ID>/download?attachment` (IDs about 924-954 on the mountain page; the link title holds the file name, e.g. Elk-Knob.pdf); two exceptions use `/kings-creek/download?attachment`. No map dates on the page (A). Rules: regulation links exist, none per game land (A): https://www.ncwildlife.gov/hunt/fishing-hunting-trapping-regulations.
- **State parks (ncparks.gov):** `ncparks.gov/maps/<park>-state-park-map/open` ok 36 of 37 (A, bot). Dates not stated.
- **State trails:** trails.nc.gov/maps/map-pdfs-<trail>/open (ok).
- Handovers: none seen.
