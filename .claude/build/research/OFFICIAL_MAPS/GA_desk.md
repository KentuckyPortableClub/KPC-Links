# US-GA official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| gastateparks.org | 50 | 47 | `gastateparks.org/sites/default/files/parks/pdf/trailmaps/<file.pdf>` | US-2165 A. H. Stephens State Park: https://gastateparks.org/sites/default/files/parks/pdf/trailmaps/AHStephens_TrailMap.pdf → ok; date not stated<br>US-2167 Black Rock Mountain State Pa: https://gastateparks.org/sites/default/files/parks/pdf/trailmaps/parkmaps/black_rock_mountain_sp_2022_sitemap.jpg → ok; date not stated<br>US-2168 Chattahoochee Bend State Par: https://gastateparks.org/sites/default/files/parks/pdf/trailmaps/parkmaps/chattahoochee bend sp 2022 map.jpg → no answer (URL can't contain control characters. '/); date not stated |
| nps.gov | 10 | 10 | `nps.gov/chat/planyourvisit/<file.htm>` | US-0662 Chattahoochee River National: https://www.nps.gov/chat/planyourvisit/maps.htm → ok; date Various map dates; Island Ford updated May 2026<br>US-0663 Cumberland Island National S: https://www.nps.gov/cuis/planyourvisit/maps.htm → ok; date not stated<br>US-0711 Kennesaw Mountain National B: https://www.nps.gov/kemo/planyourvisit/maps.htm → ok; date not stated |
| sam.usace.army.mil | 3 | 0 | `sam.usace.army.mil/Portals/46/docs/recreation/OP-WP/Docs/<file.pdf>` | US-7883 West Point Wildlife Manageme: http://www.sam.usace.army.mil/Portals/46/docs/recreation/OP-WP/Docs/WestPointHuntingMap2012[1].pdf → HTTP 403; date not stated<br>US-7911 Lake Walter F. George Wildli: http://www.sam.usace.army.mil/Portals/46/docs/recreation/WFG/docs/Lake.pdf → HTTP 403; date not stated<br>US-9786 Lake Seminole Wildlife Manag: http://www.sam.usace.army.mil/Portals/46/docs/recreation/OP-AC-WS/images/080718-A-KI945-124.jpg → HTTP 403; date not stated |
| piedmont.fws.gov | 1 | 0 | `piedmont.fws.gov/<file.html>` | US-0264 Piedmont National Wildlife R: http://piedmont.fws.gov/pdmmap.html → HTTP 530; date not stated |
| fs.usda.gov | 1 | 0 | `fs.usda.gov/detailfull/conf/landmanagement/resourcemanagement/<page>` | US-4473 Chattahoochee-Oconee Nationa: https://www.fs.usda.gov/detailfull/conf/landmanagement/resourcemanagement/?cid=fsm9_029305 → HTTP 403; date not stated |
| exploregeorgia.org | 1 | 0 | `exploregeorgia.org/sites/default/files/listing_documents/<file.pdf>` | US-7882 Doerun Pitcherplant Bog Wild: https://www.exploregeorgia.org/sites/default/files/listing_documents/Doerun-PP-Bog-wma-map.pdf → HTTP 403; date Revised 2011 |

**Totals:** 66 park map links, 57 bot-ok (86%).

## BOT LOOK-UP (script-loaded or failed links)
- gastateparks.org: 3 of 50 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- sam.usace.army.mil: 3 of 3 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- piedmont.fws.gov: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- fs.usda.gov: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- exploregeorgia.org: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency
