# US-AK official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| nps.gov | 18 | 18 | `nps.gov/alag/planyourvisit/<file.htm>` | US-0002 Alagnak Wild River National : https://www.nps.gov/alag/planyourvisit/maps.htm → ok; date not stated<br>US-0003 Aniakchak National Preserve: https://www.nps.gov/ania/planyourvisit/maps.htm → ok; date not stated<br>US-0022 Denali National Park: https://www.nps.gov/dena/planyourvisit/maps.htm → ok; date not stated |
| blm.gov | 1 | 1 | `blm.gov/sites/blm.gov/files/documents/files/<file.pdf>` | US-11828 Fortymile BLM Wild and Sceni: https://www.blm.gov/sites/blm.gov/files/documents/files/Maps_GeoPDF_Fortymile_Wild_Scenic_River_Taylor_Highway_20170324.pdf → ok; date not stated |

**Totals:** 19 park map links, 19 bot-ok (100%).

## BOT LOOK-UP (script-loaded or failed links)
- none from this pass

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency
