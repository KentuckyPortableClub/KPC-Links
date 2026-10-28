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

## Desk research Oct 28
- **DNREC wildlife areas:** 'Wildlife Area Maps and Regulations' https://dnrec.delaware.gov/fish-wildlife/wildlife-areas/ (A; the individual files are not in the page text: BOT). Maps updated in 2016 per news (B). State parks: destateparks.com link failed for the bot (0 of 1): BOT LOOK-UP. State GIS: apps.firstmap.delaware.gov/apps/rest/services/DNREC/DNREC_Offline_Layers/MapServer/11 'Wildlife Area Boundaries'; enterprise.firstmap.delaware.gov .../Society/DE_State_Lands/MapServer/0 (B) - to chat 9. Handovers: none seen.
