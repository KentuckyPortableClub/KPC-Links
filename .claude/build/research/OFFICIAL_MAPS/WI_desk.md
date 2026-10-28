# US-WI official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| dnr.wisconsin.gov | 3 | 3 | `dnr.wisconsin.gov/topic/parks/richardbong/<page>` | US-4265 Richard Bong State Recreatio: https://dnr.wisconsin.gov/topic/parks/richardbong/maps → ok; date Map dates not stated<br>US-4352 Kettle Moraine State Forest: https://dnr.wisconsin.gov/topic/parks/kms/maps → ok; date Map dates not stated<br>US-5643 Lower Wisconsin State Riverw: https://dnr.wisconsin.gov/topic/lands/lowerwisconsin/maps → ok; date Map dates not stated |
| nps.gov | 2 | 2 | `nps.gov/apis/planyourvisit/<file.htm>` | US-0764 Apostle Islands National Lak: https://www.nps.gov/apis/planyourvisit/maps.htm → ok; date not stated<br>US-4238 Ice Age National Scenic Trai: https://www.nps.gov/iatr/planyourvisit/maps.htm → ok; date Page last updated 2026 (map date not stated) |

**Totals:** 5 park map links, 5 bot-ok (100%).

## BOT LOOK-UP (script-loaded or failed links)
- none from this pass

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency

## Desk research Oct 28
- **Wisconsin DNR:** per-property maps page `https://dnr.wisconsin.gov/topic/parks/<slug>/maps` (e.g. amnicon, fenley, govnelson, govthompson) (A). Each map links to a Widen asset page `https://widnr.widen.net/s/<random id>/<map-name>` (A): the id is random, so a bot must read it from the maps page. Older direct files also exist: `dnr.wi.gov/sites/default/files/topic/Parks/<name>.pdf` (B). No dates on the page; one hunting map slug has "2000" in it (A, meaning unclear). Rules: no rules link on the maps page (A).
- **State GIS:** dnrmaps.wi.gov/arcgis2/rest/services/PR_Recreation/PR_WSPS_Property_Info_WTM_Ext/MapServer (B) - to chat 9. Statewide map page https://dnr.wisconsin.gov/topic/lands/maps.html (B). 2026 public access lands atlas (March 2026 news) (B).
- Handovers: none seen.
