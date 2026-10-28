# US-NJ official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| state.nj.us | 61 | 61 | `state.nj.us/dep/fgw/pdf/wmamaps/<file.pdf>` | US-11337 Hamburg Mountain Wildlife Ma: https://www.state.nj.us/dep/fgw/pdf/wmamaps/hamburg_mt.pdf → ok; date not stated<br>US-11863 Butterfly Bogs Wildlife Mana: https://www.state.nj.us/dep/fgw/pdf/wmamaps/butterfly_bogs.pdf → ok; date not stated<br>US-11964 Peaslee Wildlife Management : https://www.state.nj.us/dep/fgw/pdf/wmamaps/peaslee.pdf → ok; date not stated |
| nj.gov | 43 | 3 | `nj.gov/dep/parksandforests/maps/<file.pdf>` | US-11338 Stow Creek State Park: https://nj.gov/dep/parksandforests/maps/stowcreek-area.pdf → HTTP 404; date not stated<br>US-1607 Allaire State Park: https://nj.gov/dep/parksandforests/maps/allaire-area.pdf → HTTP 404; date not stated<br>US-1608 Allamuchy Mountain State Par: https://nj.gov/dep/parksandforests/maps/allamuchy-area.pdf → HTTP 404; date not stated |
| nps.gov | 10 | 10 | `nps.gov/gate/planyourvisit/<file.htm>` | US-0680 Gateway National Recreation : https://www.nps.gov/gate/planyourvisit/maps.htm → ok; date Island unit maps have individual update dates<br>US-0684 Lower Delaware National Wild: https://www.nps.gov/lode/planyourvisit/maps.htm → ok; date Page last updated April 1, 2026<br>US-0746 Morristown National Historic: https://www.nps.gov/morr/planyourvisit/maps.htm → ok; date not stated |
| fws.gov | 1 | 1 | `fws.gov/refuge/wallkill-river/<page>` | US-0456 Wallkill River National Wild: https://www.fws.gov/refuge/wallkill-river/visit-us → ok; date not stated |
| seepassaiccounty.org | 1 | 1 | `seepassaiccounty.org/wp-content/uploads/2022/12/<file.pdf>` | US-6462 Garret Mountain Reservation : https://seepassaiccounty.org/wp-content/uploads/2022/12/Garret_122022.pdf → ok; date December 2022 |
| dep.nj.gov | 1 | 1 | `dep.nj.gov/wp-content/uploads/njnlt/<file.pdf>` | US-8047 Paulinskill Wildlife Managem: https://dep.nj.gov/wp-content/uploads/njnlt/hyper_humus.pdf → ok; date not stated |
| njpalisades.org | 1 | 1 | `njpalisades.org/pdfs/<file.pdf>` | US-8319 Palisades Interstate Park: https://www.njpalisades.org/pdfs/map.pdf → ok; date Map date not stated |

**Totals:** 118 park map links, 78 bot-ok (66%).

## BOT LOOK-UP (script-loaded or failed links)
- nj.gov: 40 of 43 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency

## Desk research Oct 28
- **Fish & Wildlife WMAs:** `state.nj.us/dep/fgw/pdf/wmamaps/<name>.pdf` (61 of 61 ok, A) and road maps `nj.gov/dep/fgw/pdf/wmaroadmaps/<name>_rd.pdf` (B); year folders exist for old guides (`/pdf/2011/`, `/pdf/2013/`, B) so a copy can be old.
- **Parks and Forestry:** `nj.gov/dep/parksandforests/maps/<name>-area.pdf`: only 3 of 43 of these links opened for the bot (A): a lot are dead or the host blocks the bot - BOT LOOK-UP, re-harvest from the parks pages (https://www.nj.gov/dep/parksandforests/). Map dates: none shown.
- Handovers: none seen.
