# US-DE official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| documents.dnrec.delaware.gov | 1 | 1 | `documents.dnrec.delaware.gov/parks/Information/Documents/Tri-ValleyTrail/<file.pdf>` | US-1743 White Clay Creek State Park: https://documents.dnrec.delaware.gov/parks/Information/Documents/Tri-ValleyTrail/White%20Clay%20State%20Park%20Trail%20Plan.pdf → ok; date Map date not stated |
| destateparks.com | 1 | 0 | `destateparks.com/wwwroot/maps/trap-pond/<file.pdf>` | US-9890 James Branch State Nature Pr: https://destateparks.com/wwwroot/maps/trap-pond/JamesBranchCanoeTrailMap.pdf → HTTP 404; date not stated |

**Totals:** 2 park map links, 1 bot-ok (50%).

## BOT LOOK-UP (script-loaded or failed links)
- destateparks.com: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency
