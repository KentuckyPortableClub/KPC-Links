# US-LA official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| nps.gov | 3 | 3 | `nps.gov/jela/planyourvisit/<file.htm>` | US-0040 Jean Lafitte National Histor: https://www.nps.gov/jela/planyourvisit/maps.htm → ok; date not stated<br>US-0729 Cane River Creole National H: https://www.nps.gov/cari/planyourvisit/maps.htm → ok; date not stated<br>US-0958 Poverty Point National Monum: https://www.nps.gov/popo/planyourvisit/maps.htm → ok; date not stated |

**Totals:** 3 park map links, 3 bot-ok (100%).

## BOT LOOK-UP (script-loaded or failed links)
- none from this pass

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency
