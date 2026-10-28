# US-OR official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| blm.gov | 15 | 15 | `blm.gov/sites/blm.gov/files/docs/2022-03/<file.pdf>` | US-10008 Klamath Hills BLM Recreation: https://www.blm.gov/sites/blm.gov/files/docs/2022-03/orwa-klamath-hills-rec-area-map.pdf → ok; date not stated<br>US-10009 Row River National Recreatio: https://www.blm.gov/sites/blm.gov/files/documents/files/nwo_rowrivertrail_brochure.pdf → ok; date not stated<br>US-10017 Quartzville Creek BLM Wild a: https://www.blm.gov/sites/default/files/documents/files/nwo_quartzvillecorridor_brochure.pdf → ok; date not stated |
| nps.gov | 8 | 8 | `nps.gov/crla/planyourvisit/<file.htm>` | US-0018 Crater Lake National Park: https://www.nps.gov/crla/planyourvisit/maps.htm → ok; date not stated<br>US-0054 Nez Perce National Historica: https://www.nps.gov/nepe/planyourvisit/maps.htm → ok; date not stated<br>US-0583 Lewis and Clark National Wil: https://www.nps.gov/lewi/planyourvisit/maps.htm → ok; date not stated |
| fs.usda.gov | 5 | 5 | `fs.usda.gov/crgnsa/<page>` | US-0731 Columbia River Gorge Nationa: https://www.fs.usda.gov/crgnsa/maps → ok; date Map date not stated<br>US-4378 Deschutes National Forest: https://www.fs.usda.gov/r06/deschutes/maps-guides → ok; date Map dates vary by map<br>US-4385 Umatilla National Forest: https://www.fs.usda.gov/r06/umatilla/maps-guides → ok; date not stated |
| stateparks.oregon.gov | 3 | 3 | `stateparks.oregon.gov/ckFiles/files/<file.pdf>` | US-10007 Oregon Coast State Trail: https://stateparks.oregon.gov/ckFiles/files/OCT-Map-1.pdf → ok; date not stated<br>US-9557 Jasper State Recreation Area: https://stateparks.oregon.gov/index.cfm?do=park.profile&parkId=178 → ok; date PDF map dated 2019-12-16<br>US-9980 Willamette River Greenway an: https://stateparks.oregon.gov/index.cfm?do=park.profile&parkId=194 → ok; date Map date not stated |
| nwp.usace.army.mil | 3 | 0 | `nwp.usace.army.mil/Locations/WillametteValley/<file.aspx>` | US-9143 Detroit Lake State Recreatio: http://www.nwp.usace.army.mil/Locations/WillametteValley/Detroit.aspx → HTTP 403; date not stated<br>US-9146 Fall Creek State Recreation : http://www.nwp.usace.army.mil/Locations/WillametteValley/FallCreek.aspx → HTTP 403; date not stated<br>US-9541 Dexter State Recreation Area: http://www.nwp.usace.army.mil/Locations/WillametteValley/Dexter.aspx → HTTP 403; date not stated |
| fws.gov | 1 | 1 | `fws.gov/refuge/umatilla/<page>` | US-0596 Umatilla National Wildlife R: https://www.fws.gov/refuge/umatilla/visit-us → ok; date not stated |

**Totals:** 35 park map links, 32 bot-ok (91%).

## BOT LOOK-UP (script-loaded or failed links)
- nwp.usace.army.mil: 3 of 3 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency
