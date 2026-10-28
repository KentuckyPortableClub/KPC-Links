# US-MD official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| nps.gov | 17 | 17 | `nps.gov/nace/planyourvisit/<file.htm>` | US-0654 National Capital Parks Park: https://www.nps.gov/nace/planyourvisit/maps.htm → ok; date not stated<br>US-0666 Catoctin Mountain Park: https://www.nps.gov/cato/planyourvisit/maps.htm → ok; date not stated<br>US-0667 Fort Washington Park: https://www.nps.gov/fowa/planyourvisit/maps.htm → ok; date not stated |
| dnr.maryland.gov | 5 | 4 | `dnr.maryland.gov/publiclands/Documents/<file.pdf>` | US-1573 Gambrill State Park: https://dnr.maryland.gov/publiclands/Documents/Gambrill_map.pdf → ok; date not stated<br>US-1574 Gathland State Park: https://dnr.maryland.gov/publiclands/pages/parkmaps/gathlandmap.aspx → ok; date Map date not stated<br>US-1588 Patapsco Valley State Park: https://dnr.maryland.gov/publiclands/Pages/central/PatapscoValley/Trail-Maps.aspx → ok; date Map dates not stated |
| home.nps.gov | 1 | 1 | `home.nps.gov/fomc/planyourvisit/<file.htm>` | US-0928 Fort McHenry National Monume: https://home.nps.gov/fomc/planyourvisit/maps.htm → ok; date Page last updated September 21, 2026 |

**Totals:** 23 park map links, 22 bot-ok (96%).

## BOT LOOK-UP (script-loaded or failed links)
- dnr.maryland.gov: 1 of 5 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency
