# US-CA official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| parks.ca.gov | 181 | 173 | `parks.ca.gov/pages/464/files/<file.pdf>` | US-1121 Ahjumawi Lava Springs State : https://www.parks.ca.gov/pages/464/files/AhjumawiLavaSpringsWeb2016.pdf → ok; date not stated<br>US-1122 Andrew Molera State Park: https://www.parks.ca.gov/pages/582/files/Andrew_Molera_Trail_Camp_Map_FINAL_(JS_12.19.22).pdf → ok; date not stated<br>US-1123 Angel Island State Park: https://www.parks.ca.gov/pages/468/files/AngelIslandSPSpanishWebLayout2016.pdf → ok; date not stated |
| nps.gov | 27 | 27 | `nps.gov/chis/planyourvisit/<file.htm>` | US-0014 Channel Islands National Par: https://www.nps.gov/chis/planyourvisit/maps.htm → ok; date not stated<br>US-0021 Death Valley National Park: https://www.nps.gov/deva/planyourvisit/maps.htm → ok; date not stated<br>US-0041 Joshua Tree National Park: https://www.nps.gov/jotr/planyourvisit/maps.htm → ok; date not stated |
| fs.usda.gov | 8 | 8 | `fs.usda.gov/htnf/<page>` | US-4391 Humboldt-Toiyabe National Fo: https://www.fs.usda.gov/htnf/ → ok; date not stated<br>US-4453 Angeles National Forest: https://www.fs.usda.gov/angeles/maps-pubs → ok; date Map date varies by map; not stated on landing page<br>US-4454 Cleveland National Forest: https://www.fs.usda.gov/r05/cleveland/maps-guides → ok; date not stated |
| blm.gov | 4 | 3 | `blm.gov/visit-us/search-details/13421/<page>` | US-11017 Little Picacho Wilderness Ar: https://www.blm.gov/visit-us/search-details/13421/2 → HTTP 404; date not stated<br>US-4541 Carrizo Plain National Monum: https://www.blm.gov/documents/california/public-room/brochure/carrizo-plain-national-monument-recreation-map-and-guide → ok; date not stated<br>US-4543 Mojave Trails National Monum: https://www.blm.gov/sites/default/files/docs/2023-07/MojaveTrailsNM_508_0.pdf → ok; date not stated |
| wildlife.ca.gov | 2 | 2 | `wildlife.ca.gov/Lands/Places-to-Visit/<page>` | US-12681 Spenceville State Wildlife A: https://wildlife.ca.gov/Lands/Places-to-Visit/Spenceville-WA → ok; date not stated<br>US-7377 Bolsa Chica Ecological Reser: https://wildlife.ca.gov/Lands/Places-to-Visit/Bolsa-Chica-ER → ok; date not stated |
| fws.gov | 1 | 1 | `fws.gov/refuge/don-edwards-san-francisco-bay/<page>` | US-0189 Don Edwards San Francisco Ba: https://www.fws.gov/refuge/don-edwards-san-francisco-bay/visit-us → ok; date Map date not stated |
| spn.usace.army.mil | 1 | 0 | `spn.usace.army.mil/Missions/Recreation/<file.aspx>` | US-10403 Lake Sonoma State Wildlife A: http://www.spn.usace.army.mil/Missions/Recreation/LakeSonoma.aspx → HTTP 403; date not stated |
| ohv.parks.ca.gov | 1 | 0 | `ohv.parks.ca.gov/pages/1170/files/<file.pdf>` | US-10633 Carnegie State Recreation Ar: https://ohv.parks.ca.gov/pages/1170/files/Resource Management Areas in Carnegie SVRA.pdf → no answer (URL can't contain control characters. '/); date not stated |
| spk.usace.army.mil | 1 | 0 | `spk.usace.army.mil/Portals/12/documents/parks_lakes/BlackButte/<file.pdf>` | US-12616 Black Butte Lake Park: http://www.spk.usace.army.mil/Portals/12/documents/parks_lakes/BlackButte/BBL_Trail_Map.pdf → HTTP 403; date not stated |
| files.santaclaracounty.gov | 1 | 0 | `files.santaclaracounty.gov/migrated/<file.pdf>` | US-3473 Martial Cottle Park State Re: https://files.santaclaracounty.gov/migrated/MartialCottleGuideMap.pdf → HTTP 403; date Map date not stated |
| dbw.parks.ca.gov | 1 | 0 | `dbw.parks.ca.gov/pages/28702/files/<file.pdf>` | US-3532 Picacho State Recreation Are: http://dbw.parks.ca.gov/pages/28702/files/BlythetoImperial.pdf → HTTP 522; date not stated |
| fire.ca.gov | 1 | 0 | `fire.ca.gov/what-we-do/natural-resource-management/forestry/<page>` | US-4607 Mountain Home Demonstration : https://www.fire.ca.gov/what-we-do/natural-resource-management/forestry/forest-management → HTTP 403; date not stated |

**Totals:** 229 park map links, 214 bot-ok (93%).

## BOT LOOK-UP (script-loaded or failed links)
- parks.ca.gov: 8 of 181 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- blm.gov: 1 of 4 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- spn.usace.army.mil: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- ohv.parks.ca.gov: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- spk.usace.army.mil: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- files.santaclaracounty.gov: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- dbw.parks.ca.gov: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- fire.ca.gov: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency
