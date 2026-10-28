# US-OH official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| dam.assets.ohio.gov | 15 | 15 | `dam.assets.ohio.gov/image/upload/ohiodnr.gov/documents/parks/parkmaps/<file.pdf>` | US-1933 Alum Creek State Park: https://dam.assets.ohio.gov/image/upload/ohiodnr.gov/documents/parks/parkmaps/alumcreekparkmap.pdf → ok; date Map date not stated in retrieved map text<br>US-1940 Caesar Creek State Park: https://dam.assets.ohio.gov/image/upload/ohiodnr.gov/documents/parks/parkmaps/caesarcreektrailmap.pdf → ok; date Rev 04/2025<br>US-1946 Delaware State Park: https://dam.assets.ohio.gov/image/upload/ohiodnr.gov/documents/parks/parkmaps/delawareparkmap.pdf → ok; date Rev. 05/2025 |
| nps.gov | 8 | 8 | `nps.gov/cuva/planyourvisit/<file.htm>` | US-0020 Cuyahoga Valley National Par: https://www.nps.gov/cuva/planyourvisit/maps.htm → ok; date Page last updated June 10, 2026<br>US-0732 Dayton Aviation Heritage Nat: https://www.nps.gov/daav/planyourvisit/maps.htm → ok; date Page last updated February 1, 2018; map date not stated<br>US-0737 Hopewell Culture National Hi: https://www.nps.gov/hocu/planyourvisit/maps.htm → ok; date not stated |
| ohiodnr.gov | 3 | 3 | `ohiodnr.gov/static/documents/parks/parkmaps/<file.pdf>` | US-1937 Buck Creek State Park: https://ohiodnr.gov/static/documents/parks/parkmaps/buckcreekparkmap.pdf → ok; date not stated<br>US-5454 Yellow Creek State Forest: https://ohiodnr.gov/go-and-do/plan-a-visit/find-a-property/yellow-creek-state-forest → ok; date not stated<br>US-7850 Caesar Creek Lake State Wild: https://ohiodnr.gov/static/documents/wildlife/wildlife-area-maps/caesarcreek.pdf → ok; date Map date not stated |
| clevelandmetroparks.com | 1 | 1 | `clevelandmetroparks.com/getmedia/3496c101-b5d3-44f1-b19c-7ddff3907e44/<file.pdf>` | US-1942 Cleveland Lakefront State Pa: https://www.clevelandmetroparks.com/getmedia/3496c101-b5d3-44f1-b19c-7ddff3907e44/Lakefront-Reservation-Map.pdf → ok; date Map date not stated |
| lrp.usace.army.mil | 1 | 0 | `lrp.usace.army.mil/Portals/72/docs/Recreation/<file.jpg>` | US-9485 Mosquito Creek State Wildlif: http://www.lrp.usace.army.mil/Portals/72/docs/Recreation/Mosquitomap.jpg → HTTP 400; date not stated |

**Totals:** 28 park map links, 27 bot-ok (96%).

## BOT LOOK-UP (script-loaded or failed links)
- lrp.usace.army.mil: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency

## Desk research Oct 28
- **ODNR (parks AND Division of Wildlife):** all files on one asset host: `dam.assets.ohio.gov/image/upload/ohiodnr.gov/documents/parks/parkmaps/<name>.pdf` (state parks, hunting maps, region maps; e.g. tarhollowhuntingmap.pdf, jesseowensregionmap.pdf) and `.../documents/wildlife/wildlife-area-maps/<name>.pdf` (e.g. Wallace_Odowd_Trimble.pdf) (A: opened the Wallace one). Bot ok 15 of 15 (A). File-name case varies, so read the saved link; never build the name.
- **Map date:** the PDF itself shows "Date Published: 5/3/2022" (A, Wallace Odowd Trimble map) - a publication date, not a revision date. Agency named only by the legend ("ODNR Lands") and wildohio.gov.
- **Rules:** Ohio Administrative Code 1501:31-15-04 (wildlife area rules) at codes.ohio.gov (B); ODNR rules pages not opened.
- **State GIS for outlines:** gis2.ohiodnr.gov/arcgis/rest/services/DOW_Services/... (B) - to chat 9.
- Handovers: none seen. Historic sites: Ohio History Connection runs the state's historic sites, not ODNR (C); boundaries not checked.
