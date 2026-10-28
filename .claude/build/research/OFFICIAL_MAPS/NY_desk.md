# US-NY official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| parks.ny.gov | 47 | 47 | `parks.ny.gov/sites/default/files/<file.pdf>` | US-10034 Bennington Battlefield State: https://parks.ny.gov/sites/default/files/BenningtonBattlefieldBenningtonHuntingMap.pdf → ok; date not stated<br>US-10081 Long Point (Thousand Islands: https://parks.ny.gov/sites/default/files/2026-09/LongPointTI_Hunting_Map.pdf → ok; date not stated<br>US-10082 Two Rivers State Park: https://parks.ny.gov/sites/default/files/2026-09/TwoRivers_Hunting_Map.pdf → ok; date not stated |
| nps.gov | 21 | 21 | `nps.gov/sara/planyourvisit/<file.htm>` | US-0062 Saratoga National Historical: https://www.nps.gov/sara/planyourvisit/maps.htm → ok; date not stated<br>US-0679 Fire Island National Seashor: https://www.nps.gov/fiis/planyourvisit/maps.htm → ok; date not stated<br>US-0763 Women's Rights National Hist: https://www.nps.gov/wori/planyourvisit/maps.htm → ok; date not stated |
| dec.ny.gov | 2 | 2 | `dec.ny.gov/nature/forests-trees/forest-preserve/<page>` | US-2001 Adirondack State Park: https://dec.ny.gov/nature/forests-trees/forest-preserve/welcome-to-the-adirondacks → ok; date not stated<br>US-5694 Balsam Lake Mountain Wild St: https://dec.ny.gov/places/balsam-lake-mountain-wild-forest → ok; date not stated |
| staffportal.parks.ny.gov | 1 | 0 | `staffportal.parks.ny.gov/parks/wellesleyisland/<file.aspx>` | US-2157 Wellesley Island State Park: https://staffportal.parks.ny.gov/parks/wellesleyisland/maps.aspx → HTTP 404; date Map dates not stated |
| empiretrail.ny.gov | 1 | 1 | `empiretrail.ny.gov/<page>` | US-8098 Empire State Trail: https://empiretrail.ny.gov/ → ok; date not stated |
| lrp.usace.army.mil | 1 | 0 | `lrp.usace.army.mil/Portals/72/docs/Recreation/<file.jpg>` | US-9037 Allegheny Reservoir Wildlife: http://www.lrp.usace.army.mil/Portals/72/docs/Recreation/101122-A-0000H-023.jpg → HTTP 400; date not stated |

**Totals:** 73 park map links, 71 bot-ok (97%).

## BOT LOOK-UP (script-loaded or failed links)
- staffportal.parks.ny.gov: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- lrp.usace.army.mil: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency

## Desk research Oct 28
- **NY State Parks (OPRHP):** files `parks.ny.gov/documents/parks/<ParkName><Kind>Map.pdf` or `parks.ny.gov/sites/default/files/<Name>…Map.pdf` (hunting maps, trail maps, e.g. PixleyFallsHuntingMap.pdf); bot ok 47 of 47 (A). Date is printed on the map: "produced by NYSOPRHP GIS Bureau, September 22, 2016" (A). So some are ten years old.
- **DEC (wildlife areas, forests):** DEC pages and viewers (Hunt Planner on ArcGIS Experience, DECinfo Locator); PDFs `dec.ny.gov/sites/default/files/<name>map.pdf` (B). WMU map file is old ("09") (A). Open data: Wildlife Management Areas on data.amerigeoss.org (B) - to chat 9. staffportal.parks.ny.gov link failed (a staff site, not public): BOT LOOK-UP.
- Handovers: none seen.
