# US-MI official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| nps.gov | 6 | 6 | `nps.gov/isro/planyourvisit/<file.htm>` | US-0039 Isle Royale National Park: https://www.nps.gov/isro/planyourvisit/maps.htm → ok; date not stated<br>US-0714 River Raisin National Battle: https://www.nps.gov/rira/planyourvisit/maps.htm → ok; date not stated<br>US-0740 Keweenaw National Historical: https://www.nps.gov/kewe/planyourvisit/maps.htm → ok; date not stated |
| michigan.gov | 5 | 0 | `michigan.gov/recsearch/-/media/Project/Websites/recsearch/documents/MapsI-N/<file.pdf>` | US-13184 Iron Belle State Trail: https://www.michigan.gov/recsearch/-/media/Project/Websites/recsearch/documents/MapsI-N/Iron_Belle_Trail.pdf?hash=AF1DE25252BE6A19A2ECED0E000690F3&rev=4b5da54922134c478354414e88875732 → HTTP 403; date Map date not stated<br>US-1487 Belle Isle State Park: https://www.michigan.gov/recsearch/parks/belleisle → HTTP 403; date Map date not stated<br>US-1511 Kal-Haven Trail State Park: https://www.michigan.gov/recsearch/-/media/Project/Websites/recsearch/documents/MapsI-N/KalHavenTrail.pdf?hash=EF06B7A2974AD7316CBF8635600319C5&rev=1ab54ca4b9a54bf68a9eabe270649539 → HTTP 403; date Map date not stated |
| dnr.state.mi.us | 1 | 0 | `dnr.state.mi.us/publications/pdfs/RecreationCamping/<file.pdf>` | US-1518 Maybury State Park: https://www.dnr.state.mi.us/publications/pdfs/RecreationCamping/maybury_map.pdf → HTTP 404; date Map date not stated |
| www2.dnr.state.mi.us | 1 | 0 | `www2.dnr.state.mi.us/Publications/PDFS/RecreationCamping/<file.pdf>` | US-3310 Fort Custer State Recreation: https://www2.dnr.state.mi.us/Publications/PDFS/RecreationCamping/fort_custer_map.pdf → HTTP 404; date Map date not stated |

**Totals:** 13 park map links, 6 bot-ok (46%).

## BOT LOOK-UP (script-loaded or failed links)
- michigan.gov: 5 of 5 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- dnr.state.mi.us: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- www2.dnr.state.mi.us: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency
