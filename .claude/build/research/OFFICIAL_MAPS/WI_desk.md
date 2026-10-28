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
