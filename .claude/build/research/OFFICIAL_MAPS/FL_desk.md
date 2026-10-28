# US-FL official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| floridastateparks.org | 11 | 3 | `floridastateparks.org/parks-and-trails/<page>` | US-1847 Collier-Seminole State Park: https://www.floridastateparks.org/parks-and-trails/collier-seminole-state-park → HTTP 403; date Map date not stated<br>US-1848 Colt Creek State Park: https://www.floridastateparks.org/parks-and-trails/colt-creek-state-park → HTTP 403; date Map date not stated<br>US-1873 Fred Gannon Rocky Bayou Stat: https://www.floridastateparks.org/sites/default/files/media/file/fgr-brochure.pdf → ok; date Map date not stated |
| nps.gov | 7 | 7 | `nps.gov/drto/planyourvisit/<file.htm>` | US-0023 Dry Tortugas National Park: https://www.nps.gov/drto/planyourvisit/maps.htm → ok; date not stated<br>US-0024 Everglades National Park: https://www.nps.gov/ever/planyourvisit/maps.htm → ok; date not stated<br>US-0659 Big Cypress National Preserv: https://www.nps.gov/bicy/planyourvisit/maps.htm → ok; date Map date not stated |
| myfwc.com | 3 | 3 | `myfwc.com/recreation/lead/babcockwebb/planning-your-visit/<page>` | US-6291 Fred C. Babcock/Cecil M. Web: https://myfwc.com/recreation/lead/babcockwebb/planning-your-visit/ → ok; date Map date not stated<br>US-6309 Hilochee Wildlife Management: https://myfwc.com/recreation/lead/hilochee/planning-your-visit/ → ok; date Map date not stated<br>US-6324 Split Oak Forest Wildlife Ar: https://myfwc.com/recreation/lead/split-oak-forest/planning-your-visit/ → ok; date not stated |
| fs.usda.gov | 2 | 1 | `fs.usda.gov/detail/florida/maps-pubs/<page>` | US-4471 Ocala National Forest: https://www.fs.usda.gov/detail/florida/maps-pubs/?cid=stelprdb5192625 → ok; date Map date varies by map<br>US-4559 Florida Trail National Sceni: https://www.fs.usda.gov/detailfull/fnst → HTTP 404; date not stated |
| fdacs.gov | 2 | 2 | `fdacs.gov/Forest-Wildfire/Our-Forests/State-Forests/<page>` | US-4632 Myakka State Forest: https://www.fdacs.gov/Forest-Wildfire/Our-Forests/State-Forests/Myakka-State-Forest → ok; date Forest map dated June 2024<br>US-4646 Withlacoochee State Forest: https://www.fdacs.gov/content/download/40669/file/Withlacoocheestateforest-entireforest.pdf → ok; date not stated |
| aws.sjrwmd.com | 2 | 2 | `aws.sjrwmd.com/SJRWMD/lands/trailguides/<file.pdf>` | US-8353 Lake Apopka North Shore Stat: https://aws.sjrwmd.com/SJRWMD/lands/trailguides/lake-apopka-north-shore-trail-map.pdf → ok; date not stated<br>US-8375 Three Forks State Conservati: https://aws.sjrwmd.com/SJRWMD/lands/recreation/Three_Forks_Conservation_Area.pdf → ok; date Map date not stated |
| fws.gov | 1 | 1 | `fws.gov/media/<page>` | US-0249 Merritt Island National Wild: https://www.fws.gov/media/merritt-island-nwr-rules-regulations-and-map → ok; date Map date not stated |
| floridadep.gov | 1 | 1 | `floridadep.gov/sites/default/files/<file.pdf>` | US-3627 General James A. Van Fleet S: https://floridadep.gov/sites/default/files/VanFleetStateTrail.pdf → ok; date PDF published approx. 2011; map date not stated |
| www5.swfwmd.state.fl.us | 1 | 0 | `www5.swfwmd.state.fl.us/greenswamp/<page>` | US-5330 Green Swamp Wilderness Park : https://www5.swfwmd.state.fl.us/greenswamp/map → no answer (<urlopen error [SSL: CERTIFICATE_VERIFY_); date Map date not stated |
| swfwmd.state.fl.us | 1 | 1 | `swfwmd.state.fl.us/sites/default/files/recreation/maps/<file.pdf>` | US-6700 Sawgrass Lake Park State Con: https://www.swfwmd.state.fl.us/sites/default/files/recreation/maps/sawgrass.pdf → ok; date Map date not stated |

**Totals:** 31 park map links, 21 bot-ok (68%).

## BOT LOOK-UP (script-loaded or failed links)
- floridastateparks.org: 8 of 11 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- fs.usda.gov: 1 of 2 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- www5.swfwmd.state.fl.us: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency

## Desk research Oct 28
- **State parks (floridastateparks.org, run by Florida DEP):** per-park page `https://www.floridastateparks.org/parks-and-trails/<park-slug>/trail-maps` or `/park-maps` or `/maps-publications` (three names in use, A). Maps are GeoPDFs behind a "Download Park Map" button; the real file address is not in the page text (A), so a browser bot must read the button. No map date on the page, only the page footer year and notices (A). Rules page: "Rules & Regulations" and "Fees" links under "Plan your visit" on every park page (A). The bot got 403 from these pages: BOT LOOK-UP, real browser.
- **Other FL agencies from the bot data:** FWC (myfwc.com/recreation/lead/<area>/planning-your-visit/), FDACS state forests (fdacs.gov/Forest-Wildfire/Our-Forests/State-Forests/<name>; Myakka page states "Forest map dated June 2024"), water-management districts (aws.sjrwmd.com/SJRWMD/lands/...pdf). Handovers: none seen.
- BOT LOOK-UP: floridastateparks.org "Download Park Map" file address for 3 parks (Big Shoals, Maclay Gardens, Hontoon Island).
