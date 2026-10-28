# US-WY official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| nps.gov | 5 | 5 | `nps.gov/grte/planyourvisit/<file.htm>` | US-0031 Grand Teton National Park: https://www.nps.gov/grte/planyourvisit/maps.htm → ok; date not stated<br>US-0817 Fort Laramie National Histor: https://www.nps.gov/fola/planyourvisit/maps.htm → ok; date not stated<br>US-0920 Devils Tower National Monume: https://www.nps.gov/deto/planyourvisit/maps.htm → ok; date not stated |
| fs.usda.gov | 2 | 1 | `fs.usda.gov/r02/blackhills/<page>` | US-4524 Black Hills National Forest: https://www.fs.usda.gov/r02/blackhills/maps-guides → ok; date not stated<br>US-6146 Cloud Peak Wilderness Area: https://www.fs.usda.gov/visit/destination/cloud-peak-wilderness → HTTP 404; date not stated |
| blm.gov | 1 | 0 | `blm.gov/style/medialib/blm/wy/field-offices/lander/<file.gif>` | US-6187 South Pass Historic Mining A: http://www.blm.gov/style/medialib/blm/wy/field-offices/lander/pics.Par.5515.Image.620.869.1.gif → HTTP 404; date not stated |

**Totals:** 8 park map links, 6 bot-ok (75%).

## BOT LOOK-UP (script-loaded or failed links)
- fs.usda.gov: 1 of 2 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- blm.gov: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency
