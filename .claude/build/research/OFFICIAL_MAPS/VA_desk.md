# US-VA official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| dcr.virginia.gov | 35 | 33 | `dcr.virginia.gov/state-parks/document/<file.pdf>` | US-1290 Bear Creek Lake State Park: https://www.dcr.virginia.gov/state-parks/document/bc-campground-map.pdf → ok; date not stated<br>US-1293 Caledon State Park: https://www.dcr.virginia.gov/state-parks/document/data/caledon-geo-map.pdf → ok; date not stated<br>US-1295 Claytor Lake State Park: https://www.dcr.virginia.gov/state-parks/document/cl-5k-brochure.pdf → ok; date not stated |
| nps.gov | 15 | 15 | `nps.gov/colo/planyourvisit/<file.htm>` | US-0016 Colonial National Historical: https://www.nps.gov/colo/planyourvisit/maps.htm → ok; date not stated<br>US-0064 Shenandoah National Park: https://www.nps.gov/shen/planyourvisit/maps.htm → ok; date Some individual trail maps updated; no single map year<br>US-0691 Prince William Forest Park: https://www.nps.gov/prwi/planyourvisit/maps.htm → ok; date not stated |
| home.nps.gov | 1 | 1 | `home.nps.gov/mana/planyourvisit/<file.htm>` | US-0712 Manassas National Battlefiel: https://home.nps.gov/mana/planyourvisit/maps.htm → ok; date Page last updated October 25, 2021 |
| virginiastateparks.gov | 1 | 0 | `virginiastateparks.gov/state-parks/document/data/<file.pdf>` | US-1299 First Landing State Park: https://www.virginiastateparks.gov/state-parks/document/data/trail-guide-firstlanding.pdf → no answer (<urlopen error [SSL: CERTIFICATE_VERIFY_); date Map date not stated |
| services.dwr.virginia.gov | 1 | 1 | `services.dwr.virginia.gov/arcgis/rest/services/Public/BirdingWildlifeTrail/<page>` | US-9935 Virginia Bird & Wildlife Sta: https://services.dwr.virginia.gov/arcgis/rest/services/Public/BirdingWildlifeTrail/MapServer → ok; date not stated |

**Totals:** 53 park map links, 50 bot-ok (94%).

## BOT LOOK-UP (script-loaded or failed links)
- dcr.virginia.gov: 2 of 35 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- virginiastateparks.gov: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency
