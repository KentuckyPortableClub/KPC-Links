# US-MN official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| nps.gov | 5 | 5 | `nps.gov/voya/planyourvisit/<file.htm>` | US-0067 Voyageurs National Park: https://www.nps.gov/voya/planyourvisit/maps.htm → ok; date not stated<br>US-0939 Grand Portage National Monum: https://www.nps.gov/grpo/planyourvisit/maps.htm → ok; date not stated<br>US-0957 Pipestone National Monument: https://www.nps.gov/pipe/planyourvisit/maps.htm → ok; date not stated |
| files.dnr.state.mn.us | 4 | 4 | `files.dnr.state.mn.us/maps/state_parks/<file.pdf>` | US-2482 Fort Snelling State Park: https://files.dnr.state.mn.us/maps/state_parks/spk00154_summer.pdf → ok; date © 2023<br>US-7145 Minnesota Valley State Recre: https://files.dnr.state.mn.us/maps/state_parks/sra00304.pdf → ok; date 2025<br>US-9384 Minnesota Valley State Trail: https://files.dnr.state.mn.us/maps/state_parks/sra00304.pdf → ok; date PDF published approx. 2025; printed map date not clearly sta |
| fws.gov | 1 | 1 | `fws.gov/refuge/minnesota-valley/visit-us/<page>` | US-0364 Minnesota Valley National Wi: https://www.fws.gov/refuge/minnesota-valley/visit-us/trails → ok; date Map date not stated |

**Totals:** 10 park map links, 10 bot-ok (100%).

## BOT LOOK-UP (script-loaded or failed links)
- none from this pass

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency
