# US-TX official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| tpwd.texas.gov | 81 | 81 | `tpwd.texas.gov/publications/pwdpubs/media/<file.pdf>` | US-10509 Sam Houston National Forest : https://tpwd.texas.gov/publications/pwdpubs/media/pwd_bk_w7000_0112a.pdf → ok; date 2025–2026 edition<br>US-13588 Post Oak Ridge State Park: https://tpwd.texas.gov/publications/pwdpubs/media/park_maps/pwd_mp_p4507_0186d.pdf → ok; date not stated<br>US-2983 Abilene State Park: https://tpwd.texas.gov/publications/pwdpubs/media/park_maps/pwd_mp_p4506_001f.pdf → ok; date not stated |
| nps.gov | 14 | 14 | `nps.gov/bibe/planyourvisit/<file.htm>` | US-0006 Big Bend National Park: https://www.nps.gov/bibe/planyourvisit/maps.htm → ok; date not stated<br>US-0035 Guadalupe Mountains National: https://www.nps.gov/gumo/planyourvisit/maps.htm → ok; date not stated<br>US-0687 Amistad National Recreation : https://www.nps.gov/amis/planyourvisit/maps.htm → ok; date not stated |
| fws.gov | 3 | 3 | `fws.gov/refuge/attwater-prairie-chicken/visit-us/<page>` | US-0542 Attwater Prairie Chicken Nat: https://www.fws.gov/refuge/attwater-prairie-chicken/visit-us/trails → ok; date not stated<br>US-0543 Balcones Canyonlands Nationa: https://www.fws.gov/refuge/balcones-canyonlands/visit-us → ok; date not stated<br>US-0548 Hagerman National Wildlife R: https://www.fws.gov/media/hagerman-national-wildlife-refuge-map-1 → ok; date Map created 03/03/2022 |
| fs.usda.gov | 1 | 1 | `fs.usda.gov/texas/<page>` | US-4417 Sam Houston National Forest: https://www.fs.usda.gov/texas/maps-pubs → ok; date Map date varies by map; not stated on landing page |
| tfsweb.tamu.edu | 1 | 0 | `tfsweb.tamu.edu/uploadedFiles/FRD/<file.pdf>` | US-4422 W. Goodrich Jones State Fore: https://tfsweb.tamu.edu/uploadedFiles/FRD/WG_Jones_Forest_Map_Color.pdf → HTTP 404; date Map date not stated |
| dallascounty.org | 1 | 0 | `dallascounty.org/Assets/uploads/docs/plandev/trails/<file.pdf>` | US-4423 Spring Creek Forest State Pr: https://www.dallascounty.org/Assets/uploads/docs/plandev/trails/25-SpringCreekGarland.pdf → HTTP 404; date not stated |
| parkplanning.nps.gov | 1 | 1 | `parkplanning.nps.gov/<file.cfm>` | US-4568 El Camino Real de los Tejas : https://parkplanning.nps.gov/document.cfm?documentID=19543 → ok; date not stated |
| swf-wc.usace.army.mil | 1 | 1 | `swf-wc.usace.army.mil/cooper/Information/<file.asp>` | US-6550 Cooper Wildlife Management A: http://www.swf-wc.usace.army.mil/cooper/Information/Maps.asp → ok; date not stated |
| thc.texas.gov | 1 | 1 | `thc.texas.gov/historic-sites/<page>` | US-6559 Fort McKavett State Historic: https://thc.texas.gov/historic-sites/fort-mckavett-state-historic-site → ok; date not stated |

**Totals:** 104 park map links, 102 bot-ok (98%).

## BOT LOOK-UP (script-loaded or failed links)
- tfsweb.tamu.edu: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- dallascounty.org: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency
