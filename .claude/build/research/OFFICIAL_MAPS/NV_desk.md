# US-NV official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| nps.gov | 2 | 2 | `nps.gov/grba/planyourvisit/<file.htm>` | US-0032 Great Basin National Park: https://www.nps.gov/grba/planyourvisit/maps.htm → ok; date not stated<br>US-0974 Tule Springs Fossil Beds Nat: https://www.nps.gov/tusk/planyourvisit/maps.htm → ok; date not stated |
| blm.gov | 2 | 2 | `blm.gov/documents/nevada/public-room/brochure/<page>` | US-13151 Shoshone OHV Trail System BL: https://www.blm.gov/documents/nevada/public-room/brochure/shoshone-ohv-trail-system-brochure → ok; date not stated<br>US-7494 Red Rock Canyon National Con: https://www.blm.gov/sites/blm.gov/files/documents/files/NV_RedRockCanyon_NCA_0.pdf → ok; date not stated |

**Totals:** 4 park map links, 4 bot-ok (100%).

## BOT LOOK-UP (script-loaded or failed links)
- none from this pass

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency
