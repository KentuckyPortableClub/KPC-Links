# US-HI official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| nps.gov | 6 | 6 | `nps.gov/havo/planyourvisit/<file.htm>` | US-0037 Hawai'i Volcanoes National P: https://www.nps.gov/havo/planyourvisit/maps.htm → ok; date not stated<br>US-0043 Kalaupapa National Historica: https://www.nps.gov/kala/planyourvisit/maps.htm → ok; date not stated<br>US-0129 Pearl Harbor National Wildli: https://www.nps.gov/valr/planyourvisit/maps.htm → ok; date not stated |
| dlnr.hawaii.gov | 2 | 1 | `dlnr.hawaii.gov/dsp/parks/hawaii/akaka-falls-state-park/<page>` | US-2208 Akaka Falls State Park: https://dlnr.hawaii.gov/dsp/parks/hawaii/akaka-falls-state-park/ → ok; date not stated<br>US-6401 Mauna Kea State Recreation A: https://dlnr.hawaii.gov/dsp/parks/oahu/mauna-kea-state-recreation-area/ → HTTP 404; date not stated |
| fws.gov | 1 | 1 | `fws.gov/refuge/hawaiian-islands/<page>` | US-0119 Hawaiian Islands National Wi: https://www.fws.gov/refuge/hawaiian-islands/visit-us → ok; date not stated |

**Totals:** 9 park map links, 8 bot-ok (89%).

## BOT LOOK-UP (script-loaded or failed links)
- dlnr.hawaii.gov: 1 of 2 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency
