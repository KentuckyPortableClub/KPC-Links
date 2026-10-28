# US-NE official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| nps.gov | 5 | 5 | `nps.gov/mnrr/planyourvisit/<file.htm>` | US-0675 Missouri National Recreation: https://www.nps.gov/mnrr/planyourvisit/maps.htm → ok; date Map date not stated<br>US-0900 Agate Fossil Beds National M: https://www.nps.gov/agfo/planyourvisit/maps.htm → ok; date not stated<br>US-0942 Homestead National Historica: https://www.nps.gov/home/planyourvisit/maps.htm → ok; date not stated |
| lpsnrd.maps.arcgis.com | 5 | 5 | `lpsnrd.maps.arcgis.com/apps/MapJournal/<file.html>` | US-4016 Cottontail Wildlife Manageme: https://lpsnrd.maps.arcgis.com/apps/MapJournal/index.html?appid=a07535d5d2f64bffbef4ca2ec6c8cd0e&section=2 → ok; date not stated<br>US-4019 Wild Plum Wildlife Managemen: https://lpsnrd.maps.arcgis.com/apps/MapJournal/index.html?appid=a07535d5d2f64bffbef4ca2ec6c8cd0e&section=8 → ok; date not stated<br>US-4020 Timber Point Wildlife Manage: https://lpsnrd.maps.arcgis.com/apps/MapJournal/index.html?appid=a07535d5d2f64bffbef4ca2ec6c8cd0e&section=7 → ok; date not stated |
| papionrd.org | 1 | 0 | `papionrd.org/wp-content/uploads/2025/06/<file.pdf>` | US-4011 Chalco Hills State Recreatio: https://www.papionrd.org/wp-content/uploads/2025/06/pPNRD-0031_MAP_Chalco_09-12.pdf → HTTP 403; date PDF posted June 2025; map date not stated |
| lenrd.org | 1 | 0 | `lenrd.org/<page>` | US-4039 Maple Creek State Recreation: http://www.lenrd.org/maple-creek-recreation-area → HTTP 404; date not stated |
| nwo.usace.army.mil | 1 | 0 | `nwo.usace.army.mil/Missions/DamandLakeProjects/MissouriRiverDams/GavinsPoint/<file.aspx>` | US-9360 Lewis and Clark Lake State R: http://www.nwo.usace.army.mil/Missions/DamandLakeProjects/MissouriRiverDams/GavinsPoint/BoatingRecreationMaps.aspx → HTTP 403; date not stated |

**Totals:** 13 park map links, 10 bot-ok (77%).

## BOT LOOK-UP (script-loaded or failed links)
- papionrd.org: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- lenrd.org: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- nwo.usace.army.mil: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency

## Desk research Oct 28
- **Nebraska Game and Parks:** open GIS page https://outdoornebraska.gov/Maps/ lists interactive maps (public access, state parks, trails...) but no REST addresses (A); "for reference only", no licence named (A). Park maps are PDFs "on each park's page" (A); the Park Areas layer is in the BTAA catalog https://geo.btaa.org/catalog/ba20d669b821473089a5d542b54f9771_0 (B). Guides: https://outdoornebraska.gov/guides (B); the Public Access Atlas by sheet (B). Natural Resources Districts (lpsnrd.maps.arcgis.com 5 of 5 ok; papionrd.org, lenrd.org failed) run their own areas. Dates: none on the page.
- Handovers: none seen. Rules: not opened.
