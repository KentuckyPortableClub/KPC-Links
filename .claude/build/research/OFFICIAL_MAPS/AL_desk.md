# US-AL official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| outdooralabama.com | 15 | 8 | `outdooralabama.com/sites/default/files/Wildlife/wildlife-management-areas/2025-2026/<file.pdf>` | US-10428 Walls of Jericho State Natur: https://www.outdooralabama.com/sites/default/files/Wildlife/wildlife-management-areas/2025-2026/2025_26_D2-James%20D.%20Martin-Skyline%20WMA.pdf → HTTP 404; date not stated<br>US-11033 The Portland Landing Conserv: https://www.outdooralabama.com/sites/default/files/Wildlife/wildlife-management-areas/2021-2022/SOA/SOA-%20portland.pdf → ok; date not stated<br>US-11272 Mulberry Fork Wildlife Manag: https://www.outdooralabama.com/sites/default/files/Wildlife/wildlife-management-areas/2025-2026/2025_26_D3-Mulberry%20Fork%20WMA.pdf → HTTP 404; date not stated |
| nps.gov | 11 | 11 | `nps.gov/liri/planyourvisit/<file.htm>` | US-0641 Little River Canyon National: https://www.nps.gov/liri/planyourvisit/maps.htm → ok; date not stated<br>US-0642 Natchez Trace Parkway Nation: https://www.nps.gov/natr/planyourvisit/maps.htm → ok; date not stated<br>US-0719 Horseshoe Bend National Mili: https://www.nps.gov/hobe/planyourvisit/maps.htm → ok; date not stated |
| alabamaforeverwild.com | 5 | 5 | `alabamaforeverwild.com/sites/default/files/<file.pdf>` | US-11026 The Indian Mountain Conserva: https://www.alabamaforeverwild.com/sites/default/files/Indian-Mountain-Complex-Permit-Map-2025-2026.pdf → ok; date not stated<br>US-11032 Old Cahawba Prairie Conserva: https://www.alabamaforeverwild.com/sites/default/files/Old-Cahawba-Prairie-Tract-Permit-Map-2025-2026.pdf → ok; date not stated<br>US-3696 Lillian Swamp Complex Preser: https://www.alabamaforeverwild.com/sites/default/files/Lillian-Swamp-Complex-Permit-Map-2025-2026.pdf → ok; date not stated |
| conservationgis.alabama.gov | 4 | 4 | `conservationgis.alabama.gov/Documents/<file.pdf>` | US-1034 Blue Springs State Park: https://conservationgis.alabama.gov/Documents/NoHunting.pdf → ok; date not stated<br>US-1036 Cathedral Caverns State Park: https://conservationgis.alabama.gov/Documents/NoHunting.pdf → ok; date not stated<br>US-3709 Turkey Creek Nature Preserve: https://conservationgis.alabama.gov/Documents/NoHunting.pdf → ok; date not stated |
| alapark.com | 3 | 3 | `alapark.com/sites/default/files/2020-02/<file.pdf>` | US-1042 Gulf State Park: https://www.alapark.com/sites/default/files/2020-02/Gulf%20State%20Park%20Map_2020.pdf → ok; date 2020<br>US-1048 Monte Sano State Park: https://www.alapark.com/maps-directory → ok; date not stated<br>US-1049 Oak Mountain State Park: https://www.alapark.com/sites/default/files/2019-07/OMSPparkmap_0.pdf → ok; date 2019 file upload; map date not stated |
| fws.gov | 1 | 1 | `fws.gov/sites/default/files/documents/<file.pdf>` | US-0161 Wheeler National Wildlife Re: https://www.fws.gov/sites/default/files/documents/Wheeler%20Map%20Digital%20File%20-%202022.12.17.pdf → ok; date 2022-12-17 |
| tva.com | 1 | 0 | `tva.com/environment/recreation/recreation-areas/<page>` | US-12412 TVA Rockpile Recreation Area: https://www.tva.com/environment/recreation/recreation-areas/rockpile-recreation-area → HTTP 403; date not stated |
| fs.usda.gov | 1 | 1 | `fs.usda.gov/r08/alabama/<page>` | US-4451 Tuskegee National Forest: https://www.fs.usda.gov/r08/alabama/maps-guides → ok; date not stated |

**Totals:** 41 park map links, 33 bot-ok (80%).

## BOT LOOK-UP (script-loaded or failed links)
- outdooralabama.com: 7 of 15 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- tva.com: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency
