# CA-AB official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| geospatial.alberta.ca | 95 | 95 | `geospatial.alberta.ca/titan/rest/services/boundary/parks_protected_areas_alberta/<page>` | CA-0653 Hilliard's Bay Provincial Pa: https://geospatial.alberta.ca/titan/rest/services/boundary/parks_protected_areas_alberta/MapServer → ok; date not stated<br>CA-0671 Rumsey Natural Area: https://geospatial.alberta.ca/titan/rest/services/boundary/parks_protected_areas_alberta/MapServer → ok; date not stated<br>CA-0677 Spray Valley Provincial Park: https://geospatial.alberta.ca/titan/rest/services/boundary/parks_protected_areas_alberta/MapServer → ok; date not stated |
| albertaparks.ca | 15 | 15 | `albertaparks.ca/media/123323/<file.pdf>` | CA-0655 Long Lake Provincial Park: https://www.albertaparks.ca/media/123323/long-lake-tear-sheet.pdf → ok; date not stated<br>CA-0672 Saskatoon Island Provincial : https://www.albertaparks.ca/media/123338/saskatoon-island-tear-sheet.pdf → ok; date not stated<br>CA-0687 William A. Switzer Provincia: https://www.albertaparks.ca/media/6492882/switzer-park-brochure.pdf → ok; date not stated |
| calgary.ca | 2 | 2 | `calgary.ca/content/dam/www/transportation/tp/documents/cycling/<file.pdf>` | CA-3046 Inglewood Bird Sanctuary: https://www.calgary.ca/content/dam/www/transportation/tp/documents/cycling/inglewood-bird-sanctuary.pdf → ok; date not stated<br>CA-3089 Nose Hill Park Natural Area: https://www.calgary.ca/content/dam/www/csps/parks/documents/construction/nose-hill-project/trail-pathways-map.pdf → ok; date not stated |
| parks.canada.ca | 1 | 1 | `parks.canada.ca/pn-np/ab/waterton/visit/cartes-maps/~/media/<file.ashx>` | CA-3157 Waterton-Glacier Internation: https://parks.canada.ca/pn-np/ab/waterton/visit/cartes-maps/~/media/bddfcc88d8744c629e94b432625ae743.ashx → ok; date not stated |

**Totals:** 113 park map links, 113 bot-ok (100%).

## BOT LOOK-UP (script-loaded or failed links)
- none from this pass

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency

## Desk research Oct 28 (Canada)
- Agency: Alberta Parks (albertaparks.ca) and Alberta Environment (alberta.ca). Page https://www.alberta.ca/public-land-recreation-maps.aspx (A, opened) lists trail and Public Land Use Zone maps only, not provincial park maps; files live at open.alberta.ca/publications/<slug>.
- Dates: page published 2026-10-05; file names carry codes like 'fp-03-2026' (A). The existing 95 geospatial.alberta.ca links in parkinfo-web.json are the real park-map source: keep that pattern.
- Status: READY for a bot for geospatial.alberta.ca links; licence not stated on the page (A).
