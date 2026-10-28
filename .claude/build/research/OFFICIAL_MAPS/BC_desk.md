# CA-BC official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| parks.canada.ca | 1 | 1 | `parks.canada.ca/lhn-nhs/bc/fortroddhill/visit/<page>` | CA-4787 Fisgard Lighthouse National : https://parks.canada.ca/lhn-nhs/bc/fortroddhill/visit/plandusite-sitemap → ok; date not stated |

**Totals:** 1 park map links, 1 bot-ok (100%).

## BOT LOOK-UP (script-loaded or failed links)
- none from this pass

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency

## Desk research Oct 28 (Canada)
- Agency: BC Parks (bcparks.ca). List page: https://bcparks.ca/plan-your-trip/maps/ (A, opened). Printable park maps sit on each park's own page under 'maps and location' (B, page text only). Two interactive ArcGIS maps on governmentofbc.maps.arcgis.com hold park boundaries (A).
- Date method: none published on the page. Treat as NO DATE; bot records the day it read the PDF.
- Rules: page disclaimer only ('may not reflect current closures'). Rules page per park (BOT LOOK-UP: confirm /park/<slug>/ pattern).
- Status: NEEDS A BROWSER BOT (park pages load maps by script). Outline source: BC Data Catalogue 'BC Parks, Ecological Reserves, and Protected Areas' (BOT LOOK-UP: confirm REST address + licence; Open Government Licence - BC expected, C).
- Historic sites agency: Heritage BC / Parks Canada; not checked (C).
