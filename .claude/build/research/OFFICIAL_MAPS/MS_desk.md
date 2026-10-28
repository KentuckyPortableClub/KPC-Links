# US-MS official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| nps.gov | 8 | 8 | `nps.gov/guis/planyourvisit/<file.htm>` | US-0661 Gulf Islands National Seasho: https://www.nps.gov/guis/planyourvisit/maps.htm → ok; date not stated<br>US-0709 Tupelo National Battlefield: https://www.nps.gov/tupe/planyourvisit/maps.htm → ok; date not stated<br>US-0715 Brices Cross Roads National : https://www.nps.gov/brcr/planyourvisit/maps.htm → ok; date not stated |
| sam.usace.army.mil | 2 | 0 | `sam.usace.army.mil/Portals/46/docs/recreation/okatibbee/<file.gif>` | US-7091 Okatibbee Wildlife Managemen: http://www.sam.usace.army.mil/Portals/46/docs/recreation/okatibbee/121022-A-AQ963-001.gif → HTTP 403; date not stated<br>US-7127 Okatibbee Lake State Recreat: http://www.sam.usace.army.mil/Portals/46/docs/recreation/okatibbee/121022-A-AQ963-001.gif → HTTP 403; date not stated |
| mdwfp.com | 1 | 0 | `mdwfp.com/wildlife-hunting/<page>` | US-7106 Leaf River Wildlife Manageme: https://www.mdwfp.com/wildlife-hunting/wma → no answer (<urlopen error [SSL: CERTIFICATE_VERIFY_); date not stated |
| mvk.usace.army.mil | 1 | 0 | `mvk.usace.army.mil/Portals/58/docs/Lakes/Mississippi/Sardis/<file.pdf>` | US-7128 Sardis Lake State Recreation: http://www.mvk.usace.army.mil/Portals/58/docs/Lakes/Mississippi/Sardis/hunt_fish_brochure_1986b.pdf → HTTP 403; date not stated |

**Totals:** 12 park map links, 8 bot-ok (67%).

## BOT LOOK-UP (script-loaded or failed links)
- sam.usace.army.mil: 2 of 2 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- mdwfp.com: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- mvk.usace.army.mil: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency

## Desk research Oct 28
- **MDWFP (wildlife areas AND state parks both on mdwfp.com):** GIS page https://www.mdwfp.com/wildlife-hunting/gis-program/ links "Interactive Mapping" and "Program Maps" but shows no file addresses, dates or rules (A). Park map example in search: `mdwfp.com/media/<number>/clarkco-state-park.pdf` (B, media-id pattern like NC). Bot got an SSL certificate error on mdwfp.com/wildlife-hunting/wma: BOT LOOK-UP (needs a browser that accepts the site's chain).
- Corps lakes (sam/mvk.usace.army.mil) all 403: BOT LOOK-UP.
- Handovers: none seen.
