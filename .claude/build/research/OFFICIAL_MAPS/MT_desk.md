# US-MT official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| nps.gov | 7 | 7 | `nps.gov/glac/planyourvisit/<file.htm>` | US-0028 Glacier National Park: https://www.nps.gov/glac/planyourvisit/maps.htm → ok; date not stated<br>US-0070 Yellowstone National Park: https://www.nps.gov/yell/planyourvisit/maps.htm → ok; date not stated<br>US-0674 Bighorn Canyon National Recr: https://www.nps.gov/bica/planyourvisit/maps.htm → ok; date not stated |
| fs.usda.gov | 3 | 0 | `fs.usda.gov/r01/bitterroot/<page>` | US-4500 Bitterroot National Forest: https://www.fs.usda.gov/r01/bitterroot/maps-guides → HTTP 403; date not stated<br>US-4505 Kootenai National Forest: https://www.fs.usda.gov/r01/kootenai/maps-guides → HTTP 403; date not stated<br>US-6209 Absaroka-Beartooth Wildernes: https://www.fs.usda.gov/visit/destination/absaroka-beartooth-wilderness → HTTP 404; date not stated |
| blm.gov | 1 | 1 | `blm.gov/visit/<page>` | US-10527 Judith Landing (BLM) Recreat: https://www.blm.gov/visit/judith-landing → ok; date not stated |
| fwp.mt.gov | 1 | 1 | `fwp.mt.gov/stateparks/<page>` | US-2605 Whitefish Lake State Park: https://fwp.mt.gov/stateparks/whitefish-lake → ok; date not stated |

**Totals:** 12 park map links, 9 bot-ok (75%).

## BOT LOOK-UP (script-loaded or failed links)
- fs.usda.gov: 3 of 3 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency
