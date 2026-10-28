# US-IN official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| in.gov | 14 | 13 | `in.gov/dnr/nature-preserves/files/<file.pdf>` | US-10247 Lawrence Creek State Nature : https://www.in.gov/dnr/nature-preserves/files/np-Lawrence_Creek.pdf → ok; date Date not stated<br>US-2252 Chain O' Lakes State Park: https://www.in.gov/dnr/state-parks/files/chain_o_lakes_trail.pdf → ok; date © 02/2026<br>US-2253 Charlestown State Park: https://www.in.gov/dnr/state-parks/files/charlestown_trail.pdf → ok; date © 01/2026 |
| nps.gov | 2 | 2 | `nps.gov/gero/planyourvisit/<file.htm>` | US-0734 George Rogers Clark National: https://www.nps.gov/gero/planyourvisit/maps.htm → ok; date not stated<br>US-0765 Indiana Dunes National Park: https://www.nps.gov/indu/planyourvisit/maps.htm → ok; date Page last updated August 27, 2024 |

**Totals:** 16 park map links, 15 bot-ok (94%).

## BOT LOOK-UP (script-loaded or failed links)
- in.gov: 1 of 14 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency

## Desk research Oct 28
- **Indiana DNR (state parks, state forests, reservoirs, fish & wildlife areas):** ONE list page https://in.gov/dnr/state-parks/maps, A-Z by property, each with a property map plus campground/hunting/trail maps (A). Links look like `https://www.in.gov/dA/<hash>/<filename>.pdf?language_id=1` (filename prefixes sp- fo- or-); a few use in.gov/dnr/... paths (A). So the file name is unguessable: a bot must read the list page. State forests also at https://in.gov/dnr/forestry/state-forest-maps2 (B).
- **Date:** none on the list; the page itself was last modified 2026-03-19 (A).
- **Rules:** https://in.gov/dnr/state-parks/property-rules-and-regulations (A).
- Manager: Indiana DNR, State Parks division (A). Handovers: none seen. Historic sites: IN DNR runs them under the same State Parks page (C).
