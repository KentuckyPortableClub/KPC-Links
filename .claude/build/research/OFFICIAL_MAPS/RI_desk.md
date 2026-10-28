# US-RI official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| dem.ri.gov | 8 | 8 | `dem.ri.gov/sites/g/files/xkgbur861/files/programs/maps/mapfile/huntingatlas/<file.pdf>` | US-6982 Big River Wildlife Managemen: https://dem.ri.gov/sites/g/files/xkgbur861/files/programs/maps/mapfile/huntingatlas/15.pdf → ok; date not stated<br>US-6983 Woody Hill Wildlife Manageme: https://dem.ri.gov/sites/g/files/xkgbur861/files/programs/naturalresources/documents/map-management-areas.pdf → ok; date not stated<br>US-6984 Black Hut Wildlife Managemen: https://dem.ri.gov/sites/g/files/xkgbur861/files/programs/naturalresources/documents/map-management-areas.pdf → ok; date not stated |
| riparks.ri.gov | 3 | 3 | `riparks.ri.gov/other-state-lands/<page>` | US-2880 Snake Den State Park: https://riparks.ri.gov/other-state-lands/snake-dendame-farm → ok; date not stated<br>US-5483 Lincoln Woods State Forest: https://riparks.ri.gov/parks/lincoln-woods-state-park → ok; date not stated<br>US-7508 Pulaski State Park: https://riparks.ri.gov/parks/pulaski-state-park → ok; date not stated |
| nps.gov | 2 | 2 | `nps.gov/rowi/planyourvisit/<file.htm>` | US-0789 Roger Williams National Memo: https://www.nps.gov/rowi/planyourvisit/maps.htm → ok; date not stated<br>US-7971 Blackstone River Valley Nati: https://www.nps.gov/blrv/planyourvisit/maps.htm → ok; date not stated |

**Totals:** 13 park map links, 13 bot-ok (100%).

## BOT LOOK-UP (script-loaded or failed links)
- none from this pass

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency
