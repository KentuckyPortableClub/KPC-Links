# US-MO official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| mdc.mo.gov | 393 | 393 | `mdc.mo.gov/media/area/map/<page>` | US-0788 Rocky Creek State Conservati: https://mdc.mo.gov/media/area/map/4629 → ok; date not stated<br>US-10110 Wire Road State Conservation: https://mdc.mo.gov/media/area/map/8307 → ok; date not stated<br>US-10116 Kings Prairie Access State C: https://mdc.mo.gov/media/area/map/8116 → ok; date not stated |
| nps.gov | 4 | 4 | `nps.gov/wicr/planyourvisit/<file.htm>` | US-0710 Wilson's Creek National Batt: https://www.nps.gov/wicr/planyourvisit/maps.htm → ok; date not stated<br>US-0779 Gateway Arch National Park: https://www.nps.gov/jeff/planyourvisit/maps.htm → ok; date not stated<br>US-0870 Ulysses S. Grant National Hi: https://www.nps.gov/ulsg/planyourvisit/maps.htm → ok; date not stated |
| nwk.usace.army.mil | 4 | 0 | `nwk.usace.army.mil/Portals/29/docs/lakesites/truman/<file.pdf>` | US-1762 Harry S Truman State Park: http://www.nwk.usace.army.mil/Portals/29/docs/lakesites/truman/Truman-LakeMap.pdf → HTTP 403; date not stated<br>US-1771 Long Branch State Park: http://www.nwk.usace.army.mil/Portals/29/docs/lakesites/longbranch/longbranch-LakeMap.pdf → HTTP 403; date not stated<br>US-1778 Pomme de Terre State Park: http://www.nwk.usace.army.mil/Portals/29/docs/lakesites/pomme/Lake%20Map-aerial.jpg → HTTP 403; date not stated |
| mvs.usace.army.mil | 2 | 0 | `mvs.usace.army.mil/Portals/54/siteimages/wappapello/maps/<file.gif>` | US-1769 Lake Wappapello State Park: http://www.mvs.usace.army.mil/Portals/54/siteimages/wappapello/maps/Lake-Map-for-web.gif → HTTP 403; date not stated<br>US-1772 Mark Twain State Park: http://www.mvs.usace.army.mil/Portals/54/docs/recreation/marktwain/maps/MTL_Map_MTL_Overall_Map.pdf → HTTP 403; date not stated |
| swl.usace.army.mil | 1 | 0 | `swl.usace.army.mil/Portals/50/docs/tablerocklake/<file.pdf>` | US-1787 Table Rock State Park: http://www.swl.usace.army.mil/Portals/50/docs/tablerocklake/TABLE%20ROCK%20MAP%203-05.pdf → HTTP 403; date not stated |

**Totals:** 404 park map links, 397 bot-ok (98%).

## BOT LOOK-UP (script-loaded or failed links)
- nwk.usace.army.mil: 4 of 4 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- mvs.usace.army.mil: 2 of 2 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- swl.usace.army.mil: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency
