# US-OK official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| swt.usace.army.mil | 4 | 0 | `swt.usace.army.mil/Locations/TulsaDistrictLakes/Oklahoma/<file.aspx>` | US-2788 Keystone State Park: http://www.swt.usace.army.mil/Locations/TulsaDistrictLakes/Oklahoma/KeystoneLake.aspx → HTTP 403; date not stated<br>US-2791 Lake Texoma State Park: http://www.swt.usace.army.mil/Portals/41/docs/lakes/texoma/TexWebR.pdf → HTTP 403; date not stated<br>US-6356 Keystone Wildlife Management: http://www.swt.usace.army.mil/Locations/TulsaDistrictLakes/Oklahoma/KeystoneLake.aspx → HTTP 403; date not stated |
| nps.gov | 3 | 3 | `nps.gov/waba/planyourvisit/<file.htm>` | US-0872 Washita Battlefield National: https://www.nps.gov/waba/planyourvisit/maps.htm → ok; date not stated<br>US-3675 Chickasaw National Recreatio: https://www.nps.gov/chic/planyourvisit/maps.htm → ok; date not stated<br>US-8115 Oklahoma City National Memor: https://www.nps.gov/okci/planyourvisit/maps.htm → ok; date not stated |

**Totals:** 7 park map links, 3 bot-ok (43%).

## BOT LOOK-UP (script-loaded or failed links)
- swt.usace.army.mil: 4 of 4 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency
