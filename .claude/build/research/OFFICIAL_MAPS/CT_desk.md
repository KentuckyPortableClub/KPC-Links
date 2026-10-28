# US-CT official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| nae.usace.army.mil | 3 | 0 | `nae.usace.army.mil/Portals/74/docs/Recreation/BRL/<file.pdf>` | US-1649 Black Rock State Park: http://www.nae.usace.army.mil/Portals/74/docs/Recreation/BRL/BRLRecMap.pdf → HTTP 403; date not stated<br>US-1694 Mansfield Hollow State Park: http://www.nae.usace.army.mil/Portals/74/docs/Recreation/MHLMap.pdf → HTTP 403; date not stated<br>US-7520 Mansfield Hollow Wildlife Ma: http://www.nae.usace.army.mil/Portals/74/docs/Recreation/MHLMap.pdf → HTTP 403; date not stated |
| nps.gov | 1 | 1 | `nps.gov/wefa/planyourvisit/<file.htm>` | US-0873 Weir Farm National Historic : https://www.nps.gov/wefa/planyourvisit/maps.htm → ok; date not stated |
| portal.ct.gov | 1 | 1 | `portal.ct.gov/-/media/DEEP/stateparks/maps/<file.pdf>` | US-1728 Wharton Brook State Park: https://portal.ct.gov/-/media/DEEP/stateparks/maps/whartonbrookpdf.pdf → ok; date January 20, 2011 |

**Totals:** 5 park map links, 2 bot-ok (40%).

## BOT LOOK-UP (script-loaded or failed links)
- nae.usace.army.mil: 3 of 3 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency

## Desk research Oct 28
- **DEEP (state parks and forests):** one list page https://portal.ct.gov/DEEP/State-Parks/Trail-and-Camping-Maps---CT-State-Parks-and-Forests (A). Files `portal.ct.gov/-/media/deep/stateparks/maps/<name>pdf.pdf?rev=&hash=` (trail maps `<name>pdf.pdf`, campground `<name>cgpdf.pdf`); `rev`/`hash` are cache ids, not dates (A). A few say 'Map is not available' (Fort Griswold, Haystack Mountain). Only date clue: a year inside a file name (sunrisestatepark_2018r.pdf). Per-forest Maps pages: `portal.ct.gov/DEEP/State-Parks/Forests/<Forest>/Maps` (B). Rules: https://portal.ct.gov/deep/state-parks/recreation-information/recreational-trail-use-information (A). Corps nae.usace.army.mil 0 of 3: BOT LOOK-UP. Handovers: none seen. Boundary data: CT ECO (cteco.uconn.edu DEEP property, B) - to chat 9.
