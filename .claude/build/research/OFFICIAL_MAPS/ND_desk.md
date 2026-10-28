# US-ND official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| nps.gov | 2 | 2 | `nps.gov/thro/planyourvisit/<file.htm>` | US-0065 Theodore Roosevelt National : https://www.nps.gov/thro/planyourvisit/maps.htm → ok; date not stated<br>US-0840 Knife River Indian Villages : https://www.nps.gov/knri/planyourvisit/maps.htm → ok; date not stated |
| nwo.usace.army.mil | 1 | 0 | `nwo.usace.army.mil/Missions/DamandLakeProjects/MissouriRiverDams/Garrison/<file.aspx>` | US-2764 Lake Sakakawea State Park: http://www.nwo.usace.army.mil/Missions/DamandLakeProjects/MissouriRiverDams/Garrison/BoatingRecreationMaps.aspx → HTTP 403; date not stated |

**Totals:** 3 park map links, 2 bot-ok (67%).

## BOT LOOK-UP (script-loaded or failed links)
- nwo.usace.army.mil: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency

## Desk research Oct 28
- **ND Game and Fish:** one index https://gf.nd.gov/maps/map-index: a table of Link / Format / Description / Category; hosts vary: ArcGIS Online (ndgf.maps.arcgis.com), Geocortex viewers (geocortex.gf.nd.gov), `gf.nd.gov/gnf/maps/...` PDFs/JPGs (A). No dates (only "updated annually" for one). Rules: gf.nd.gov/regulations (A).
- **State parks (ND Parks & Recreation):** not opened: BOT LOOK-UP. Park outlines: gis.dmr.nd.gov ND_State_Parks FeatureServer (B) - to chat 9.
- Corps (nwo.usace.army.mil) failed: BOT LOOK-UP. Handovers: none seen.
