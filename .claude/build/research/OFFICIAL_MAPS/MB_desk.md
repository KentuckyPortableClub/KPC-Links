# CA-MB official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| legacy.winnipeg.ca | 1 | 1 | `legacy.winnipeg.ca/publicworks/parks/<file.stm>` | CA-2515 St. Vital Park Recreation Pa: https://legacy.winnipeg.ca/publicworks/parks/st-vital.stm → ok; date not stated |

**Totals:** 1 park map links, 1 bot-ok (100%).

## BOT LOOK-UP (script-loaded or failed links)
- none from this pass

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency

## Desk research Oct 28 (Canada)
- Agency: Manitoba Sustainable Development. List page https://www.gov.mb.ca/sd/parks/park-maps-and-locations/ (A). Pattern: .../park-maps-and-locations/<region>/<slug>.html, regions eastern, central, northeast, northwest, western; slugs short, sometimes odd (birds, malo, stgeorge, camp_morton) so match by the region index page, not by guessing (A).
- Date: none on page (A). Rules: none on page.
- Gotcha: main list and sidebar differ (Colvin Lake, Nueltin Lake, Marchand, Poplar Bay, South Atikaki, Wallace Lake, Memorial Park only in the sidebar) so read both.
- Status: READY for a bot (read region index pages).
