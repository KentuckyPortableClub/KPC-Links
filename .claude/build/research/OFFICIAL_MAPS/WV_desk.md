# US-WV official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| wvdnr.gov | 89 | 88 | `wvdnr.gov/wmamapproj/pdf/pdf300/<file.pdf>` | US-12032 Burning Springs Wildlife Man: http://www.wvdnr.gov/wmamapproj/pdf/pdf300/BurningSpringsFinal11x17_300dpi.pdf → ok; date not stated<br>US-12033 Cheat Canyon Wildlife Manage: http://www.wvdnr.gov/wmamapproj/pdf/pdf300/CheatCanyonFinal11x17_300dpi.pdf → ok; date not stated<br>US-12035 Dents Run Wildlife Managemen: http://www.wvdnr.gov/wmamapproj/pdf/pdf300/DentsRunFinal11x17_300dpi.pdf → ok; date not stated |
| drive.google.com | 7 | 7 | `drive.google.com/file/d/1oUlv8DFUOCiyVAbR4JfIG8h6aadP8POd/<page>` | US-5582 Cabwaylingo State Forest: https://drive.google.com/file/d/1oUlv8DFUOCiyVAbR4JfIG8h6aadP8POd/view?usp=drive_link → ok; date not stated<br>US-5583 Calvin Price State Forest: https://drive.google.com/file/d/1lbPcmJQ1636eUKFwxJC_dQsFOBSMoa5a/view?usp=drive_link → ok; date not stated<br>US-5585 Coopers Rock State Forest: https://drive.google.com/file/d/1cC5BWfWaFMetZYBPWJWJOgzdWfjxQwQE/view?usp=drive_link → ok; date not stated |
| nps.gov | 4 | 4 | `nps.gov/choh/planyourvisit/<file.htm>` | US-0015 Chesapeake and Ohio Canal Na: https://www.nps.gov/choh/planyourvisit/maps.htm → ok; date Page last updated November 19, 2025<br>US-0695 Gauley River National Recrea: https://www.nps.gov/gari/planyourvisit/maps.htm → ok; date not stated<br>US-0696 New River Gorge National Par: https://www.nps.gov/neri/planyourvisit/maps.htm → ok; date not stated |
| wvstateparks.com | 2 | 2 | `wvstateparks.com/wp-content/uploads/2025/06/<file.pdf>` | US-1800 Beech Fork State Park: https://wvstateparks.com/wp-content/uploads/2025/06/2024.10.24_WVSP_BeechFork_Map_FINAL.pdf → ok; date not stated<br>US-1810 Chief Logan State Park: https://wvstateparks.com/wp-content/uploads/2020/10/ChiefLoganStateParkMap.pdf → ok; date 2020 file upload; map date not stated |
| fs.usda.gov | 1 | 0 | `fs.usda.gov/Internet/FSE_DOCUMENTS/<file.pdf>` | US-4526 George Washington & Jefferso: https://www.fs.usda.gov/Internet/FSE_DOCUMENTS/fseprd1136678.pdf → HTTP 404; date March 28, 2022 |
| avenzamaps.com | 1 | 1 | `avenzamaps.com/maps/852301/<page>` | US-6994 Burches Run Wildlife Managem: https://www.avenzamaps.com/maps/852301/burches-run-wildlife-management-area → ok; date not stated |

**Totals:** 104 park map links, 102 bot-ok (98%).

## BOT LOOK-UP (script-loaded or failed links)
- wvdnr.gov: 1 of 89 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- fs.usda.gov: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency

## Desk research Oct 28
- **WMAs (WV Division of Natural Resources, 96 areas, about 1.4 million acres):** list https://wvdnr.gov/lands-waters/wildlife-management-areas/ ; district pages `.../district-N-wildlife-management-areas/` N=1..6; statewide map `wvdnr.gov/wp-content/uploads/2022/01/WMAmap_2021_RGB.png` (the upload month = rough date) (A). Per-area PDFs: `wvdnr.gov/wmamapproj/pdf/pdf300/<Name>Final11x17_300dpi.pdf` (bot ok 88 of 89, A). Avenza/other topo versions are archived at sites.google.com/wv.gov/dnrgis/archived-maps/ (A); hunting map at mapwv.gov/huntfish/. Rules: https://wvdnr.gov/lands-waters/wildlife-management-areas/rules-and-regulations/ (A).
- **State parks and forests (wvstateparks.com):** `wvstateparks.com/wp-content/uploads/<YYYY>/<MM>/<file>.pdf` (upload month = date). Seven state forests point at Google Drive file links (ok, but a Drive link is not an agency address: ask WV for a real one).
- Handovers: none seen.
