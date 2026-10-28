# US-IL official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| dnr.illinois.gov | 5 | 3 | `dnr.illinois.gov/content/dam/soi/en/web/dnr/calendar/publishingimages/first-day-hikes/<file.pdf>` | US-1000 Illinois Beach State Park: https://dnr.illinois.gov/content/dam/soi/en/web/dnr/calendar/publishingimages/first-day-hikes/illinoisbeach.pdf → ok; date Map date not stated<br>US-1001 James Pate Philip State Park: https://dnr.illinois.gov/content/dam/soi/en/web/dnr/hunting/factsheets/documents/jamespatephiliphuntermap4.pdf → HTTP 404; date Map date not stated<br>US-10660 Illinois and Michigan Canal : https://dnr.illinois.gov/content/dam/soi/en/web/dnr/hunting/factsheets/documents/imcanaleasthuntermap.pdf → HTTP 404; date Map date not stated in search result |
| nps.gov | 3 | 3 | `nps.gov/liho/planyourvisit/<file.htm>` | US-0841 Lincoln Home National Histor: https://www.nps.gov/liho/planyourvisit/maps.htm → ok; date not stated<br>US-4572 Lewis and Clark National His: https://www.nps.gov/lecl/planyourvisit/maps.htm → ok; date Page last updated 2026 (map date not stated)<br>US-7917 Pullman National Monument: https://www.nps.gov/pull/planyourvisit/maps.htm → ok; date not stated |
| s7d1.scene7.com | 1 | 1 | `s7d1.scene7.com/is/image/isp/<page>` | US-1012 Moraine Hills State Park: https://s7d1.scene7.com/is/image/isp/morainehillsmap2026 → ok; date not stated |
| fws.gov | 1 | 1 | `fws.gov/refuge/upper-mississippi-river/<page>` | US-4236 Upper Mississippi River Nati: https://www.fws.gov/refuge/upper-mississippi-river/map → ok; date not stated |

**Totals:** 10 park map links, 8 bot-ok (80%).

## BOT LOOK-UP (script-loaded or failed links)
- dnr.illinois.gov: 2 of 5 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency
