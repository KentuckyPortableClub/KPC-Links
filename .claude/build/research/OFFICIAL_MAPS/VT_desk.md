# US-VT official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| nae.usace.army.mil | 2 | 0 | `nae.usace.army.mil/Portals/74/docs/Recreation/TSL/<file.pdf>` | US-3148 Townshend State Park: http://www.nae.usace.army.mil/Portals/74/docs/Recreation/TSL/TSLTrailMap.pdf → HTTP 403; date not stated<br>US-5528 Townshend State Forest: http://www.nae.usace.army.mil/Portals/74/docs/Recreation/TSL/TSLTrailMap.pdf → HTTP 403; date not stated |
| nps.gov | 1 | 1 | `nps.gov/mabi/planyourvisit/<file.htm>` | US-0744 Marsh-Billings-Rockefeller N: https://www.nps.gov/mabi/planyourvisit/maps.htm → ok; date not stated |
| vtstateparks.com | 1 | 1 | `vtstateparks.com/<file.html>` | US-3106 Button Bay State Park: https://vtstateparks.com/buttonbay.html → ok; date not stated |

**Totals:** 4 park map links, 2 bot-ok (50%).

## BOT LOOK-UP (script-loaded or failed links)
- nae.usace.army.mil: 2 of 2 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency

## Desk research Oct 28
- **Vermont State Parks:** publications page https://vtstateparks.com/publications (A). Maps: `vtstateparks.com/media/<number>` or `/media/document/<park>-state-park-map-and-guide` (A). No dates, except old geology maps (1987, 1962). Corps lakes (nae.usace.army.mil) 0 of 2: BOT LOOK-UP. Forests, Parks & Recreation lands beyond state parks: not looked at. Handovers: none seen.
