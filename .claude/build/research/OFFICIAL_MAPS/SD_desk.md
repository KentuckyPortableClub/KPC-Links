# US-SD official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| nps.gov | 5 | 5 | `nps.gov/badl/planyourvisit/<file.htm>` | US-0005 Badlands National Park: https://www.nps.gov/badl/planyourvisit/maps.htm → ok; date not stated<br>US-0068 Wind Cave National Park: https://www.nps.gov/wica/planyourvisit/maps.htm → ok; date not stated<br>US-0786 Mount Rushmore National Memo: https://www.nps.gov/moru/planyourvisit/maps.htm → ok; date not stated |
| nwo.usace.army.mil | 1 | 0 | `nwo.usace.army.mil/Missions/DamandLakeProjects/MissouriRiverDams/GavinsPoint/<file.aspx>` | US-8174 Lewis and Clark State Recrea: http://www.nwo.usace.army.mil/Missions/DamandLakeProjects/MissouriRiverDams/GavinsPoint/BoatingRecreationMaps.aspx → HTTP 403; date not stated |

**Totals:** 6 park map links, 5 bot-ok (83%).

## BOT LOOK-UP (script-loaded or failed links)
- nwo.usace.army.mil: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency
