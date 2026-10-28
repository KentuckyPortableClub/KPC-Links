# US-PA official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| nps.gov | 17 | 17 | `nps.gov/gett/planyourvisit/<file.htm>` | US-0027 Gettysburg National Military: https://www.nps.gov/gett/planyourvisit/maps.htm → ok; date not stated<br>US-0704 Fort Necessity National Batt: https://www.nps.gov/fone/planyourvisit/maps.htm → ok; date not stated<br>US-0733 First State National Histori: https://www.nps.gov/frst/planyourvisit/maps.htm → ok; date not stated |
| pa.gov | 9 | 9 | `pa.gov/agencies/dcnr/recreation/where-to-go/state-parks/find-a-park/french-creek-state-park/<page>` | US-1355 French Creek State Park: https://www.pa.gov/agencies/dcnr/recreation/where-to-go/state-parks/find-a-park/french-creek-state-park/maps → ok; date not stated<br>US-1387 Moraine State Park: https://www.pa.gov/agencies/dcnr/recreation/where-to-go/state-parks/find-a-park/moraine-state-park/maps → ok; date Map date not stated<br>US-1391 Nockamixon State Park: https://www.pa.gov/agencies/dcnr/recreation/where-to-go/state-parks/find-a-park/nockamixon-state-park/maps → ok; date Map date not stated on map page |
| elibrary.dcnr.pa.gov | 3 | 3 | `elibrary.dcnr.pa.gov/<file.ashx>` | US-1352 Fort Washington State Park: https://elibrary.dcnr.pa.gov/PDFProvider.ashx?PromptToSave=False&Size=4135995&ViewerMode=2&action=PDFStream&docID=1753400&docName=FOWA_ParkGuide&nativeExt=pdf&overlay=0&revision=0 → ok; date Map date not stated<br>US-1356 Gifford Pinchot State Park: https://elibrary.dcnr.pa.gov/PDFProvider.ashx?PromptToSave=False&Size=1854693&ViewerMode=2&action=PDFStream&chksum=&docID=1737648&docName=GIPI_CampgroundMap&nativeExt=pdf&overlay=0&revision=3 → ok; date Rev. 07/23/2024<br>US-1406 Prouty Place State Park: https://elibrary.dcnr.pa.gov/GetDocument?docId=1736597&DocName=sf-PUd15.pdf → ok; date not stated |

**Totals:** 29 park map links, 29 bot-ok (100%).

## BOT LOOK-UP (script-loaded or failed links)
- none from this pass

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency

## Desk research Oct 28
- **DCNR (state parks, forests):** per-park Maps page `pa.gov/agencies/dcnr/recreation/where-to-go/state-parks/find-a-park/<park>/maps` (also `state-forests/find-a-forest/<forest>/maps`); files on `http://elibrary.dcnr.pa.gov/GetDocument?docId=<number>&DocName=<file>.pdf` (A). The docId is not a date; no date on the page (A); bot ok 3 of 3 + pa.gov 9 of 9.
- **Game Commission (State Game Lands):** list https://www.pa.gov/agencies/pgc/huntingandtrapping/where-to-hunt/state-game-land-maps is a search-by-number page, links NOT in the text (A): BOT LOOK-UP (script-loaded). PGC Mapping Center: experience.arcgis.com/experience/7bc4a733a9a140879dbee399d65c165e (A). Regulations: pa.gov/agencies/pgc/huntingandtrapping/regulations (A). No dates.
- DCNR parks page has no rules link (A). Handovers: none seen.
