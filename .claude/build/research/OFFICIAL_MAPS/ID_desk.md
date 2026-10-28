# US-ID official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| nps.gov | 4 | 4 | `nps.gov/miin/planyourvisit/<file.htm>` | US-0279 Minidoka National Wildlife R: https://www.nps.gov/miin/planyourvisit/maps.htm → ok; date not stated<br>US-0665 Craters of the Moon National: https://www.nps.gov/crmo/planyourvisit/maps.htm → ok; date not stated<br>US-0940 Hagerman Fossil Beds Nationa: https://www.nps.gov/hafo/planyourvisit/maps.htm → ok; date not stated |
| blm.gov | 1 | 1 | `blm.gov/programs/national-conservation-lands/<page>` | US-10383 Jim McClure-Jerry Peak Wilde: https://www.blm.gov/programs/national-conservation-lands/idaho → ok; date not stated |
| parksandrecreation.idaho.gov | 1 | 0 | `parksandrecreation.idaho.gov/parks/lava-hot-springs/<page>` | US-11157 Lava Hot Springs State Recre: https://parksandrecreation.idaho.gov/parks/lava-hot-springs/ → HTTP 404; date not stated |

**Totals:** 6 park map links, 5 bot-ok (83%).

## BOT LOOK-UP (script-loaded or failed links)
- parksandrecreation.idaho.gov: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency
