# US-DC official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| nps.gov | 22 | 22 | `nps.gov/coga/planyourvisit/<file.htm>` | US-0653 Constitution Gardens Nationa: https://www.nps.gov/coga/planyourvisit/maps.htm → ok; date not stated<br>US-0655 National Mall Park: https://www.nps.gov/nama/planyourvisit/maps.htm → ok; date Page last updated June 26, 2025<br>US-0656 Rock Creek Park: https://www.nps.gov/rocr/planyourvisit/maps.htm → ok; date not stated |

**Totals:** 22 park map links, 22 bot-ok (100%).

## BOT LOOK-UP (script-loaded or failed links)
- none from this pass

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency

## Desk research Oct 28
- All 22 bot-checked DC links are National Park Service pages (nps.gov/<code>/planyourvisit/maps.htm, all open). DC has no state park agency in the data. Nothing else needed.
