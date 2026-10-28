# KY wild rivers + nature preserves: official pages and maps (chat 9, Oct 28 2026; HQ 12:55 PM, for chat 2's documents bot)
Read from each Office of Kentucky Nature Preserves (OKNP) page by a GitHub runner (round K4, .claude/build/research/ADDS/roundK4-tested.json). Every page IS the park's official page (already the `page` on file). What the pages hold:

**No OKNP page has its own map file.** Each page links (a) the statewide 'Kentucky Nature Preserves' map viewer `https://kygisportal.ky.gov/arcgis/apps/webappviewer/index.html?id=d57ad568a4e44cc4b7c505952f3e898f` (shared by every OKNP page: the bot is right to drop it as 'a statewide viewer') and (b) a Google Maps PIN the agency set for the park (= the agency's own location point: useful as an ACCESS / location pin, not a map). So for these parks the honest answer is **'no park map published; official location pin + statewide viewer'**, not a missing page.

| Park | Official page (on file) | Map the page links | Agency location pin (from the page's map link) |
|---|---|---|---|
| US-10105 The Green NWSR (state wild river) | eec.ky.gov/…/Green-River-Wild-River.aspx (bot saw 404 once; runner got 200) | NPS Mammoth Cave backcountry map (on file) + L&D 6 removal report (not a map) | none |
| US-10103 Cumberland River (wild river) | …/Cumberland-River-Wild-River.aspx | KDFWR **Blue Water Trail, North Fork Cumberland River** map: https://fw.ky.gov/Education/Documents/bluewatertrailnorthforkcumberlandriver.pdf (an agency water-trail map of the river: candidate 'map') | none |
| US-10106 Rockcastle (wild river) | …/Rockcastle-River-Wild-River.aspx | none of its own | 37.0278, -84.328 |
| US-10107 Big South Fork (wild river) | …/Big-South-Fork-Wild-River.aspx | NPS BISO maps page (on file) | none |
| US-10111 Rock Creek (wild river) | …/Rock-Creek-Wild-River.aspx | none of its own | 36.645189, -84.71045 |
| US-10112 Bad Branch (wild river) | …/Bad-Branch-Wild-River.aspx | none of its own | short link maps.app.goo.gl/QtSYRc6Yn8JJPFTF7 (resolving in round K5) |
| US-12752 Green River SNA | …/Rush-Island-Bottoms.aspx | none (photo only) | none (Boiling Springs pin = chat 2's unit_pins) |
| US-7955 Six Mile Island SNP | …/Six-Mile-Island.aspx | none | short link goo.gl/maps/VRUtwZS2v3tvo9JW6 (K5) |
| US-7956 Beargrass Creek SNP | …/Beargrass-Creek.aspx | none | 38.209225, -85.710854 |
| US-7960 Crooked Creek SNP | …/Crooked-Creek.aspx | none | 38.6410556, -83.5701111 |
| US-7961 Jesse Stuart SNP | …/Jesse-Stuart.aspx | none | short link goo.gl/maps/esrrSCkVcp7wPgJs9 (K5) |
| US-7962 Little South Fork SNA | …/Burnett-WWCA.aspx | none (photo only) | 36.697308, -84.71… (page link) |
| US-7964 William H. Martin SNA | …/Dr.-William-H.-Martin-WWCA.aspx | none (photo only) | none |
| US-7968 E. Lucy Braun SNP | …/E.-Lucy-Braun.aspx | none | 36.9648889, -83.11… (page link) |
OKNP's wild-rivers list also names Little South Fork, Martins Fork and Red River wild rivers (…/Little-South-Fork-Wild-River.aspx, …/Martins-Fork-Wild-River.aspx, …/Red-River-Wild-River.aspx).

**Salato (US-10172, chat 11's lead):** page https://fw.ky.gov/Education/Pages/Salato-Wildlife-Education-Center.aspx (KDFWR) answers; the trail map on file (salatotrailmap.pdf) is Salato's own trail map (the bot flagged it as 'does not name this park': it names the CENTER, which IS the park: keep it). Hours: the page text shows only notices (closed Wed Nov 11 for Veterans Day; a one-day change on Apr 3); the regular hours sit in a page part the text reader did not reach: hours = 'see the official page' until a browser pass reads them.

FOR CHAT 2: (1) mark these 14 as 'no park map published (OKNP): statewide viewer + agency pin' rather than 'no page'; (2) Cumberland River: the KDFWR Blue Water Trail PDF is the agency's river map: hand-list it as the map; (3) the agency pins can go in as access/location points (source 'OKNP page map link'); (4) Salato: keep its trail map.
