# CA-ON official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| markham.ca | 1 | 1 | `markham.ca/sites/default/files/neighbourhood-sevices/city-of-markham-cycling/<file.pdf>` | CA-1668 Toogood Pond Park Conservati: https://www.markham.ca/sites/default/files/neighbourhood-sevices/city-of-markham-cycling/FINAL-Cycling%2BMap%2B2023-aug-9-v2.pdf → ok; date not stated |

**Totals:** 1 park map links, 1 bot-ok (100%).

## BOT LOOK-UP (script-loaded or failed links)
- none from this pass

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency

## Desk research Oct 28 (Canada)
- Agency: Ontario Parks (ontarioparks.ca). Pattern (A, opened): maps page https://www.ontarioparks.ca/park/<slug>/maps ; PDF https://www.ontarioparks.ca/pdf/maps/<slug>/park_map.pdf ; rules https://www.ontarioparks.ca/park/<slug>/rules. Example tested: ladyevelynsmoothwater.
- Match a park: slug = park name lowercased, no spaces/punctuation (B from the one example; BOT LOOK-UP: test 2 more slugs).
- Date method: none in map links (A). NO DATE.
- Status: READY for a bot (pattern is plain), match by slug; outlines: Ontario GeoHub 'Provincial Park' layer (BOT LOOK-UP, C).
