# US-NM official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| nps.gov | 12 | 12 | `nps.gov/cave/planyourvisit/<file.htm>` | US-0012 Carlsbad Caverns National Pa: https://www.nps.gov/cave/planyourvisit/maps.htm → ok; date not stated<br>US-0013 Chaco Culture National Histo: https://www.nps.gov/chcu/planyourvisit/maps.htm → ok; date not stated<br>US-0752 Pecos National Historical Pa: https://www.nps.gov/peco/planyourvisit/maps.htm → ok; date not stated |
| fs.usda.gov | 2 | 0 | `fs.usda.gov/r03/cibola/<page>` | US-4514 Cibola National Forest: https://www.fs.usda.gov/r03/cibola/maps-guides → HTTP 403; date not stated<br>US-4516 Lincoln National Forest: https://www.fs.usda.gov/r03/lincoln/maps-guides → HTTP 403; date not stated |
| eplanning.blm.gov | 1 | 1 | `eplanning.blm.gov/public_projects/lup/68121/86178/103335/<file.pdf>` | US-11791 Santa Cruz Lake BLM Recreati: https://eplanning.blm.gov/public_projects/lup/68121/86178/103335/Map_08_SRMAs_+_ERMAs.pdf → ok; date not stated |
| emnrd.state.nm.us | 1 | 0 | `emnrd.state.nm.us/SPD/documents/<file.pdf>` | US-2717 Sumner Lake State Park: http://www.emnrd.state.nm.us/SPD/documents/SuLPARKMAP.pdf → no answer (<urlopen error [Errno -2] Name or servic); date not stated |

**Totals:** 16 park map links, 13 bot-ok (81%).

## BOT LOOK-UP (script-loaded or failed links)
- fs.usda.gov: 2 of 2 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- emnrd.state.nm.us: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency
