# US-SC official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| nps.gov | 8 | 8 | `nps.gov/cong/planyourvisit/<file.htm>` | US-0017 Congaree National Park: https://www.nps.gov/cong/planyourvisit/maps.htm → ok; date not stated<br>US-0702 Cowpens National Battlefield: https://www.nps.gov/cowp/planyourvisit/maps.htm → ok; date Map date not stated<br>US-0720 Kings Mountain National Mili: https://www.nps.gov/kimo/planyourvisit/maps.htm → ok; date Map date not stated |
| southcarolinaparks.com | 3 | 3 | `southcarolinaparks.com/<page>` | US-2902 Kings Mountain State Park: https://southcarolinaparks.com/maps-and-brochures → ok; date Map date not stated<br>US-2905 Lee State Park: https://southcarolinaparks.com/lee/maps-and-brochures → ok; date Map date varies by map<br>US-2913 Sesquicentennial State Park: https://southcarolinaparks.com/files/State%20Parks%20Files/Sesqui/MapSesquicentennial.pdf → ok; date Map date not stated; official park map |
| fws.gov | 1 | 1 | `fws.gov/media/<page>` | US-0522 Savannah National Wildlife R: https://www.fws.gov/media/savannah-nwr-full-and-trail-maps → ok; date Publication date listed July 9, 2026 |
| embed.widencdn.net | 1 | 1 | `embed.widencdn.net/pdf/plus/scprt/1b2dm2dbko/<file.pdf>` | US-3873 Colonial Dorchester State Hi: https://embed.widencdn.net/pdf/plus/scprt/1b2dm2dbko/CDMap_2017.pdf?u=sgt8lu → ok; date 2017 |
| fs.usda.gov | 1 | 0 | `fs.usda.gov/scnfs/<page>` | US-4522 Francis Marion National Fore: https://www.fs.usda.gov/scnfs/maps-pubs → HTTP 403; date Map date varies by map |

**Totals:** 14 park map links, 13 bot-ok (93%).

## BOT LOOK-UP (script-loaded or failed links)
- fs.usda.gov: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency

## Desk research Oct 28
- **SCDNR (wildlife areas):** list page https://www.dnr.sc.gov/wma/maps.html (A, linked from dnr.sc.gov/maps.html); old file pattern `dnr.sc.gov//wma/maps/wmamap<N>.pdf` (B, search results); public lands portal https://public-lands-scdnr.hub.arcgis.com/ (A, open-data hub: look here FIRST for outlines, RESEARCH ORDER). Regulations: https://dnr.sc.gov/regulations.html (no WMA-specific rules page, A). Dates not in the URLs.
- **State parks:** southcarolinaparks.com/maps-and-brochures and /<park>/maps-and-brochures (bot ok 3 of 3, "map date varies by map").
- Francis Marion NF page returned 403 to the bot: BOT LOOK-UP.
- Handovers: none seen.
