# US-MA official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| nps.gov | 14 | 14 | `nps.gov/caco/planyourvisit/<file.htm>` | US-0672 Cape Cod National Seashore: https://www.nps.gov/caco/planyourvisit/maps.htm → ok; date not stated<br>US-0725 Adams National Historical Pa: https://www.nps.gov/adam/planyourvisit/maps.htm → ok; date not stated<br>US-0728 Boston National Historical P: https://www.nps.gov/bost/planyourvisit/maps.htm → ok; date not stated |
| mass.gov | 2 | 1 | `mass.gov/lists/<page>` | US-2420 Borderland State Park: https://www.mass.gov/lists/dcr-trail-maps → ok; date not stated<br>US-2464 Whitehall State Park: https://www.mass.gov/locations/lake-whitehall-state-park → HTTP 404; date not stated |
| nae.usace.army.mil | 1 | 0 | `nae.usace.army.mil/Portals/74/docs/Recreation/WHD/<file.pdf>` | US-11573 West Hill Dam Wildlife Manag: http://www.nae.usace.army.mil/Portals/74/docs/Recreation/WHD/WHDProjectMap.pdf → HTTP 403; date not stated |

**Totals:** 17 park map links, 15 bot-ok (88%).

## BOT LOOK-UP (script-loaded or failed links)
- mass.gov: 1 of 2 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- nae.usace.army.mil: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency
