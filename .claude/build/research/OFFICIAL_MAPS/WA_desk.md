# US-WA official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| nps.gov | 8 | 8 | `nps.gov/mora/planyourvisit/<file.htm>` | US-0052 Mount Rainier National Park: https://www.nps.gov/mora/planyourvisit/maps.htm → ok; date not stated<br>US-0055 North Cascades National Park: https://www.nps.gov/noca/planyourvisit/maps.htm → ok; date not stated<br>US-0056 Olympic National Park: https://www.nps.gov/olym/planyourvisit/maps.htm → ok; date not stated |
| parks.wa.gov | 6 | 3 | `parks.wa.gov/find-parks/state-parks/<page>` | US-0727 Lake Lenore Caves State Park: https://parks.wa.gov/find-parks/state-parks/lake-lenore-caves-state-park → HTTP 404; date not stated<br>US-12846 Columbia Hills State Natural: https://parks.wa.gov/find-parks/state-parks/columbia-hills-state-park → HTTP 404; date not stated<br>US-3171 Spokane River Centennial Sta: https://parks.wa.gov/DocumentCenter/View/9837/Centennial-Trail-State-Park-PDF?bidId= → HTTP 404; date Date not stated |
| fs.usda.gov | 3 | 1 | `fs.usda.gov/detail/ipnf/<page>` | US-4477 Idaho Panhandle National For: https://www.fs.usda.gov/detail/ipnf/maps-pubs?cid=fsm9_019030 → HTTP 403; date not stated<br>US-4531 Okanogan-Wenatchee National : https://www.fs.usda.gov/r06/okanogan-wenatchee/data-tools/interactive-maps → HTTP 404; date Last updated June 10, 2025<br>US-4563 Pacific Northwest National S: https://www.fs.usda.gov/trails/pacific-northwest-nst → ok; date not stated |
| blm.gov | 2 | 2 | `blm.gov/sites/blm.gov/files/documents/files/<file.pdf>` | US-12245 Twin Lakes BLM Recreation Ma: https://www.blm.gov/sites/blm.gov/files/documents/files/spo_twinlakesrecarea_brochure.pdf → ok; date not stated<br>US-8664 Fishtrap National Recreation: https://www.blm.gov/sites/blm.gov/files/documents/files/spo_fishtraprecarea_brochure.pdf → ok; date not stated |

**Totals:** 19 park map links, 14 bot-ok (74%).

## BOT LOOK-UP (script-loaded or failed links)
- parks.wa.gov: 3 of 6 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- fs.usda.gov: 2 of 3 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency
