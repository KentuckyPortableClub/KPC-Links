# US-NH official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| nhstateparks.org | 4 | 2 | `nhstateparks.org/visit/historic-sites/<page>` | US-8020 Franklin Pierce Homestead St: https://www.nhstateparks.org/visit/historic-sites/franklin-pierce-homestead → HTTP 404; date not stated<br>US-8025 Wentworth- Coolidge Mansion : https://www.nhstateparks.org/visit/historic-sites/wentworth-coolidge-mansion → HTTP 404; date not stated<br>US-8028 Madison Boulder State Natura: https://www.nhstateparks.org/visit/state-parks/madison-boulder-natural-area → ok; date not stated |
| fws.gov | 1 | 1 | `fws.gov/refuge/silvio-o-conte/<page>` | US-0329 Silvio O Conte National Wild: https://www.fws.gov/refuge/silvio-o-conte/visit-us → ok; date not stated |
| nps.gov | 1 | 1 | `nps.gov/saga/planyourvisit/<file.htm>` | US-0857 Saint-Gaudens National Histo: https://www.nps.gov/saga/planyourvisit/maps.htm → ok; date not stated |
| mass.gov | 1 | 1 | `mass.gov/doc/nashua-river-rail-trail-map/<page>` | US-8396 Nashua River Rail Trail Stat: https://www.mass.gov/doc/nashua-river-rail-trail-map/download → ok; date not stated |

**Totals:** 7 park map links, 5 bot-ok (71%).

## BOT LOOK-UP (script-loaded or failed links)
- nhstateparks.org: 2 of 4 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency

## Desk research Oct 28
- **NH State Parks:** one statewide Map & Guide PDF per year: `nhstateparks.org/NHStateParks/media/NHStateParks/PDFs/Find Parks and Trails/26_NHSP_MapAndGuide_v7-2026.pdf` (B; the year is in the file name = a date clue) and the find page https://www.nhstateparks.org/find-parks-trails (B). 2 of 4 bot-checked links opened. State forest reservation maps: https://www.nhdfl.dncr.nh.gov/land-management/state-reservation-maps (B). Parks outlines: maps.dot.nh.gov NHDOT_BOUNDARIES_Parks_Forest (B) - to chat 9. Handovers: none seen.
