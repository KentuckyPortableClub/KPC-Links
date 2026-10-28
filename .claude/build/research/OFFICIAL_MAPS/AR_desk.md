# US-AR official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| agfc.com | 21 | 21 | `agfc.com/maps/<page>` | US-7266 Blue Mountain Wildlife Manag: https://www.agfc.com/maps/ → ok; date not stated<br>US-7268 Brewer Lake Wildlife Managem: https://www.agfc.com/maps/ → ok; date not stated<br>US-7269 Brushy Creek Wildlife Manage: https://www.agfc.com/maps/ → ok; date not stated |
| arkansasstateparks.com | 12 | 6 | `arkansasstateparks.com/parks/<page>` | US-1071 Arkansas Post Museam State P: https://www.arkansasstateparks.com/parks/arkansas-post-museum-state-park → HTTP 404; date not stated<br>US-1073 Cane Creek State Park: https://www.arkansasstateparks.com/parks/cane-creek-state-park → ok; date not stated<br>US-1075 Cossatot River State Park: https://www.arkansasstateparks.com/parks/cossatot-river-state-park-natural-area → ok; date not stated |
| nps.gov | 6 | 6 | `nps.gov/hosp/planyourvisit/<file.htm>` | US-0038 Hot Springs National Park: https://www.nps.gov/hosp/planyourvisit/maps.htm → ok; date not stated<br>US-0721 Pea Ridge National Military : https://www.nps.gov/peri/planyourvisit/maps.htm → ok; date not stated<br>US-0768 Arkansas Post National Memor: https://www.nps.gov/arpo/planyourvisit/maps.htm → ok; date not stated |
| swl.usace.army.mil | 5 | 0 | `swl.usace.army.mil/Missions/Recreation/ArkansasRiver/<file.aspx>` | US-1091 Lake Dardanelle State Park: http://www.swl.usace.army.mil/Missions/Recreation/ArkansasRiver/Dardanelle.aspx → HTTP 403; date not stated<br>US-7190 Bull Shoals Lake State Recre: http://www.swl.usace.army.mil/Missions/Recreation/Lakes/BullShoalsLake.aspx → HTTP 403; date not stated<br>US-7280 Dardanelle Wildlife Manageme: http://www.swl.usace.army.mil/Missions/Recreation/ArkansasRiver/Dardanelle.aspx → HTTP 403; date not stated |
| fs.usda.gov | 2 | 2 | `fs.usda.gov/r08/ouachita/<page>` | US-4424 Ouachita National Forest: https://www.fs.usda.gov/r08/ouachita/maps-guides → ok; date not stated<br>US-7442 Blanchard Springs State Recr: https://www.fs.usda.gov/recarea/osfnf/recarea/?recid=43431 → ok; date not stated |
| arkansasheritage.com | 1 | 1 | `arkansasheritage.com/docs/default-source/anhc-maps/boundary-maps/<file.pdf>` | US-0637 Mills Park State Conservatio: https://www.arkansasheritage.com/docs/default-source/anhc-maps/boundary-maps/mills-park-natural-area-boundary-map-3-18-22.pdf?sfvrsn=56454d3a_2 → ok; date not stated |
| apps.agfc.com | 1 | 0 | `apps.agfc.com/maps/<page>` | US-7294 Holland Bottoms Wildlife Man: https://apps.agfc.com/maps/ → HTTP 403; date not stated |

**Totals:** 48 park map links, 36 bot-ok (75%).

## BOT LOOK-UP (script-loaded or failed links)
- arkansasstateparks.com: 6 of 12 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- swl.usace.army.mil: 5 of 5 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- apps.agfc.com: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency

## Desk research Oct 28
- **AGFC (wildlife management areas):** maps hub https://agfc.com/en/resources/maps/ lists the Interactive Mapper (gis.agfc.com) and Public Use Maps (https://apps.agfc.com/maps/) - individual files not in the page text (A): BOT LOOK-UP apps.agfc.com/maps/. REST: gisec2.agfc.com/arcgis/rest/services/GIS/AGFC_DATA/MapServer (B) - to chat 9. **State parks:** arkansasstateparks.com and the Arkansas Heritage links (Mills Park PDF with a sfvrsn version tag) come from the bot data (48 links). No dates on the hub. Handovers: none seen.
