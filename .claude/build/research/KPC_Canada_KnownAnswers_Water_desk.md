# CANADA: KNOWN ANSWERS + WATER SOURCE CHECK (Research desk, chat 8, Oct 28 11:50 PM)
For chat 2. Grades: A = our own files, B = page opened, C = my knowledge, not opened (I cannot open agency maps or the satellite view). Park numbers and names are from data/ca-key; "bot row" = what data/fers/CA-XX.json already holds.

## 1. KNOWN ANSWERS (Canada's test; 6 sure-ish, 3 controls)
| # | Pair | Kind | Why | Grade | Bot row |
|---|---|---|---|---|---|
| 1 | CA-0010 Bruce Peninsula NP + CA-5628 Bruce Trail NRT | trail inside | The Bruce Trail runs through the park (park is on the trail's route; parks.canada.ca lists it) | C | candidate (ON, `trail@45.234,-81.410`) = agrees |
| 2 | CA-0024 Fundy Biosphere Reserve + CA-0025 Fundy NP | area (park inside reserve) | The biosphere reserve was built around Fundy National Park (UNESCO) | C | `same land@45.631,-64.997` = agrees |
| 3 | CA-0052 Long Point Biosphere Reserve + CA-0053 Long Point NWA | area (inside) | The reserve covers the whole Long Point peninsula | C | `same land` = agrees |
| 4 | CA-0052 Long Point Biosphere Reserve + CA-0279 Long Point Provincial Park | area (inside) | same | C | `same land` = agrees |
| 5 | CA-0052 + CA-0053 + CA-0279 | 3-fer (pairs 3, 4 + 0053/0279) | Rule 11: three pair rows, 3-fer on top. Whether NWA and provincial park themselves touch is NOT SURE (control, do not require it) | C | check pair 0053+0279 |
| 6 | CA-3724 Lanz and Cox Islands Prov. Park + CA-4065 Scott Islands MPA | area (islands inside the marine area) | Lanz and Cox Islands are part of the Scott Islands group the MPA covers | C | candidate, 8,429 ac = agrees |
Controls (should NOT come out as plain live):
- C1: CA-0040 Jasper NP + CA-3167 Willmore Wilderness Park (bot: 618 ac candidate, many rows). The two parks share a long border; touching is not a 2-fer. If the official maps overlap, it is a drawing slop; send to NOT SURE / very tight, not live. HARD guess.
- C2: CA-0021 Fathom Five NP + CA-5628 Bruce Trail (bot: trail candidate). Fathom Five is mostly lake and islands; the trail ends at Tobermory next to it. NOT SURE unless the trail touches Fathom Five's land (Flowerpot Island has trails but not the Bruce Trail).
- C3: CA-0711 Cape Scott PP + CA-4065 Scott Islands MPA (7,230 ac bot candidate): MPA is offshore; overlap only if the park's marine part lies in it. Check official maps; do not require.
Not enough sure examples: I don't know a Canadian "water trail / canoe route" park number from the list for certain; ask chat 9 to pull the Trans Canada Trail / Waterfront Trail rows from ca-key (CA-6003 Great Lakes Waterfront Trail is one) and open each park's route map.
Bot-row check (A): CA-AB 200 candidates, CA-ON 91, CA-NS 187 (mostly "same land", may be many sibling NWA/nature reserve pairs: spot-check), CA-QC only 3 live because 549 rows still waited for a pass.

## 2. WATER SOURCE CHECK
- **Licence (B):** NHN and CHN are both published under the **Open Government Licence – Canada** (open.canada.ca/en/open-government-licence-canada). Attribution line to carry: "Contains information licensed under the Open Government Licence – Canada." Free reuse, commercial too, no key. I only saw the licence NAME on the CHN page, not the terms text.
- **CHN replaces NHN (B)** but is not out everywhere. NRCan says CHN "is replacing the National Hydro Network"; first release Feb 2024, 30 work units, ~65,000 km² (page: New Brunswick Miramichi first; map shows NB, NS, PE, QC, ON work units). So: **use NHN as the base everywhere; use CHN only where its index says a work unit is released**. Index services: https://maps-cartes.services.geo.ca/server_serveur/rest/services/NRCan/chn_index_en/MapServer . CHN files: https://ftp.maps.canada.ca/pub/nrcan_rncan/vector/chn_rhc/workunit_unitetravail/ (GeoPackage); REST: .../NRCan/chn_en/MapServer (dataset record modified 2024-12-31, "as needed").
- I did NOT see whether CHN has waterbody polygons or river AREAS (the page doesn't say). Ask the bot to print the layer list of chn_en MapServer.
- **Where NHN lakes are weak (C, knowledge):** the north (Nunavut, NWT, Yukon) is mapped at 1:50,000 in places but 1:250,000 elsewhere, so small lakes and shorelines are rough; parts of northern QC/NL/MB the same. Lakes are fine in southern ON, QC, the Maritimes and BC. NHN river AREAS (wide rivers as polygons) exist only for larger rivers.
- **Check for the water job:** test 5 known lakes (Lake Ontario shore at Long Point, Fundy tidal flats, Lac Saint-Jean, Babine Lake BC, Great Slave Lake) against NHN index zip names; the tide zone will not match (NHN stops at the high-water line, like the US).

## 3. BOT LOOK-UP rows
| Who | Row |
|---|---|
| chat 9 | Print the layers/fields of chn_en MapServer and the chn_index_en work-unit list (released provinces, grade); report whether a waterbody polygon layer exists |
| chat 9 | For pairs 1-6 and C1-C3: open the two park pages' maps on parks.canada.ca / bcparks.ca / ontarioparks.com and say overlap / touch / apart |
| chat 2 | Run the known-answers test on pairs 1-6; C1-C3 must not come out plain live |
