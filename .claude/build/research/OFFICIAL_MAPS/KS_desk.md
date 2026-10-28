# US-KS official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| nwk.usace.army.mil | 14 | 0 | `nwk.usace.army.mil/Portals/29/docs/lakesites/clinton/<file.pdf>` | US-2332 Clinton State Park: http://www.nwk.usace.army.mil/Portals/29/docs/lakesites/clinton/Hunting-Brochure.pdf → HTTP 403; date not stated<br>US-2340 Hillsdale State Park: http://www.nwk.usace.army.mil/Portals/29/docs/lakesites/Hillsdale/hillsdale-lakemap[1].pdf → HTTP 403; date not stated<br>US-2342 Kanopolis Lake State Park: http://www.nwk.usace.army.mil/Portals/29/docs/lakesites/Kanopolis/Kanopolis-LakeMap.pdf → HTTP 403; date not stated |
| nps.gov | 3 | 3 | `nps.gov/fols/planyourvisit/<file.htm>` | US-0818 Fort Larned National Histori: https://www.nps.gov/fols/planyourvisit/maps.htm → ok; date not stated<br>US-0821 Fort Scott National Historic: https://www.nps.gov/fosc/planyourvisit/maps.htm → ok; date not stated<br>US-0851 Nicodemus National Historic : https://www.nps.gov/nico/planyourvisit/maps.htm → ok; date not stated |
| ksoutdoors.com | 3 | 0 | `ksoutdoors.com/KDWP-Info/Locations/State-Fishing-Lakes/South-Central-Region/<page>` | US-7412 Black Kettle State Fishing L: https://ksoutdoors.com/KDWP-Info/Locations/State-Fishing-Lakes/South-Central-Region/Black-Kettle → HTTP 403; date not stated<br>US-7421 Rooks State Fishing Lake: https://ksoutdoors.com/KDWP-Info/Locations/State-Fishing-Lakes/Northwest-Region/Rooks → HTTP 403; date not stated<br>US-7949 Woodson State Wildlife Area: https://ksoutdoors.com/KDWP-Info/Locations/Wildlife-Areas → HTTP 403; date not stated |

**Totals:** 20 park map links, 3 bot-ok (15%).

## BOT LOOK-UP (script-loaded or failed links)
- nwk.usace.army.mil: 14 of 14 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- ksoutdoors.com: 3 of 3 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency
