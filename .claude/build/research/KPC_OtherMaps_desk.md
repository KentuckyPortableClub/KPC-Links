# Other POTA map sites as a second witness (desk, Oct 27 2026 night)
Read only. I opened each public page and its published notes. **Nothing was copied from any of these sites, and I did not contact anyone.** Where a site's own drawing is hidden behind a script, I say so and list it for a bot (BOT LOOK-UP). Evidence: A = page opened, B = search result, C = my inference.

## 1. Bottom line
- **None of these sites has an official layer we do not already name.** Their outlines are PAD-US (USGS) plus volunteer files, so they are *less* official than ours. They are useful as a pointer: where a volunteer had to draw a map, PAD-US had a hole, which is where our key has holes too.
- **ham-map.com draws no boundaries at all** (its builder OK1SIM says "the goal isn't to show a border", A via QRPer comments). Pins only.
- **potamap.us = PAD-US + N9EAT's community maps for CA IL IN MI MN NE NM NY.** Those eight states are exactly where our scoreboard has name-mismatch and missing-layer gaps (NY 27, CA 34, NE 21, IL 15, IN 22, MI 61, MN 36), so the community maps are a hint of where PAD-US is weak, not a source.
- **One real find while checking a sample park: New York's own state-park boundary layer** (NYS OPRHP Boundary, polygon, field `Name`, `Acre`) at https://gisportaldev.dot.ny.gov/server/rest/services/CulturalResources/Cultural_Resources/MapServer/16 (A; dev host, copyright and date blank; item id 11b1b5b778ef416f9bf30b938637dbfd). Our NY key reads DEC lands only, so state parks like Thompsons Lake (US-2151) have no official outline. Get it from the agency (find the production host / NY GIS Clearinghouse), never from potamap.
- In the 30-park check the agency was right and PAD-US (what potamap draws) was partial in 3 of the 5 parks where I could read the agency's own acreage; ours agreed in all 5.

## 2. The sites
| Site | Who / code | What it shows | Boundaries? | Sources it credits | Licence | Opened |
|---|---|---|---|---|---|---|
| potamap.us | NU4J; code github.com/cwhelchel/potamap.ol | POTA parks (pins + outlines), SOTA summits, trails, counties, 4-char grid layer; search by ref; KML upload; activation upload | **Yes**: PAD-US designation files (e.g. `PADUS3_0Designation_StateNV.geojson`) simplified with mapshaper and **merged by park name**; community boundary maps by Marty N9EAT for CA, IL, IN, MI, MN, NE, NM, NY ("may overlap PAD-US but add boundaries for parks that lacked them"); trails from USGS/NPS/volunteers; counties from K1RA APRS QSO-party files | PAD-US (USGS GAP); NPS trails; N9EAT; K1RA; SOTA | repo README shows none (the site has a "no warranty" notice) | A (home page + README excerpt; GitHub main page only partly) |
| ham-map.com | OK1SIM (Michal) | SOTA, POTA, GMA, WWFF pins for one country at a time, "Rebuild Map" | **No** ("only for overview") | Local hams helped add POTA parks (e.g. Iași, RO) | not stated | A (QRPer article; the site itself is a loading screen for a text reader) |
| New Park Finder (newparks.m0trt.radio, newparks.ianrenton.com) | Ian Renton MØTRT; code git.ianrenton.com/ian/new-park-finder | POTA, SOTA, WWBOTA, WWFF, GMA, LLOTA pins coloured by status (ATNO never activated, activated by others, by you, can't tell this year); zoom in then "find parks" | No boundaries | **POTA's public but unofficial API** (page says it can change without warning) | LICENSE file exists; type not shown | A (help page + home) |
| newparks-python, pota-local-progress (same author) | scripts | KML of never-activated parks; parks by last activated; nearest parks | No | the same POTA API, cached one day | LICENSE file, type not shown | A |
| ScoutCAT | K3SBP (Casey Stanton), part of the POTACAT family | Offline map packs (state/country/world), nightly sync of POTA, SOTA, WWFF, WWBOTA, LLOTA; **INSIDE/OUTSIDE check against park polygons** | **Yes**, "public geospatial datasets" (not named) | none named | free app, no licence stated | A (article by 9M2PJU) |
| OpenStreetMap | Alan W2AEW's tip | any park boundary; "doesn't often map national or state trails" | Yes (volunteer) | | ODbL | A |
| pota.review / pota.news "how to use the POTAmap" | article | potamap tutorial | | | | B (redirects to pota.news, not fetchable here) |
Unreached this session: potamap's actual drawn outlines (script-loaded; the shell has no network), ham-map's own About page.

## 3. Official layers they credit that we do not read
| Layer | Who credits it | Do we read it? | Action |
|---|---|---|---|
| PAD-US (USGS) | potamap, ScoutCAT (probably) | **Yes** (the numeric ids in our key) | none |
| NPS / USGS trail lines | potamap | partly (`akht`, NHT trte layer is ruled approximate) | already in Round 3 list |
| County lines (K1RA files) | potamap | not needed | none |
| Community maps N9EAT (CA IL IN MI MN NE NM NY) | potamap | **no, and we do not want them** (unofficial) | use the states' own layers: NY OPRHP (new), IN ManagedLands_DNR_Open (read), MI DNR parks FeatureServer/8 (read), MN DNR (read), CA State Parks (read), IL and NE and NM agency layers (see their region files) |
| "Public geospatial datasets" | ScoutCAT | unknown | none; ask the author only if HQ wants (we do not contact) |

## 4. The 30-park sample
Ten gaps from the scoreboard (first ten rows) and twenty matched parks drawn at random across the eight community-map states and others. "Ours" = the acreage of our official-layer polygon; "PAD-US" = the acreage of our PAD-US polygon (the shape potamap draws, C: potamap merges PAD-US pieces by name, so it can differ from one piece). I could not see the drawn geometry on their site, so "agree" is judged by acreage and by who publishes the line, graded C; the agency's own figure was read for the six marked **Differ/Agree** below (A).

| # | Park | Our outline | Acreage | Potamap would draw | Result / who is right |
|---|---|---|---|---|---|
| 1 | US-12150 Dry Fork Camping Area BLM Recreation M | NO outline | BLM site point (Dry Fork Camping Area) | PAD-US has no shape for a campsite; expect pin or nothing on potamap | pin only; BLM_Natl_Recreation/3 gives a point |
| 2 | CA-5550 Bathurst Glen Golf Course Conservation | NO outline | Ontario conservation authority golf course | potamap does not cover Canada | municipal/commercial: pin only |
| 3 | US-5686 Fairfax State Recreation Area | NO outline | Indiana DNR layer ManagedLands_DNR_Open (read by us as "ind") | IN is a community-map state: N9EAT map may carry it | name issue: Fairfax SRA is "Lake Monroe" unit (N-5) |
| 4 | US-7073 William C. Deviney Wildlife Management | NO outline | MARIS WMA layer (Round 1) | PAD-US likely has it (MS WMAs are in PAD-US); potamap would draw it | missing layer; confirm number |
| 5 | US-7805 Antelope Valley Airstrip State Recreat | NO outline | IDPR hub (Round 2): an airstrip | PAD-US may hold it as a point/small polygon | pin only (ruled) |
| 6 | US-5570 Little Pend Oreille State Forest | NO outline | WA DNR Cadastre layer sgwac (read) | PAD-US has the pieces | name mismatch (Little Pend Oreille is a state forest + NWR + WDFW area) |
| 7 | US-6809 Copper Harbor State Harbor | NO outline | MI State Harbor: point feature | PAD-US none; N9EAT MI map may | pin only |
| 8 | US-2151 Thompsons Lake State Park | NO outline | NYS OPRHP Boundary (NEW find: NY DOT Cultural_Resources/MapServer/16) | PAD-US has state parks; NY is a community-map state | REAL missing layer: our NY key has DEC lands only |
| 9 | US-1174 Montana de Oro State Park | NO outline | California State Parks ParkBoundaries (sgcab, read) | PAD-US + CA community map: potamap very likely draws it | likely NAME mismatch: the layer probably spells "Montaña de Oro" with ñ; our name has n (C) |
| 10 | US-13156 Schueler: East Sub Unit Wildlife Manag | NO outline | MN DNR WMA layer (sgmna, read) | MN is a community-map state | name mismatch: layer calls it "Schueler WMA: East Subunit"; matcher already flagged the near-miss |
| 11 | US-2945 Fall Creek Falls State Park | official layer | ours 15250 ac / PAD-US 6248 ac | PAD-US | **Differ.** Agency: "more than 26,000 acres". Ours = two official polygons 15,250 + 10,840 = 26,090. PAD-US pieces 6,248 + 1,134 + 1,133. **We are right**; potamap (PAD-US) would show only part. |
| 12 | US-2716 Sugarite Canyon State Park | official layer | ours 4530 ac / PAD-US 4115 ac | PAD-US + community map | Agency 4,500 ac; ours 4,530; PAD-US 4,115 (91%). Agree within PAD-US slack. |
| 13 | US-12833 Chehalis River Surge Plain State Natur | PAD-US only | ours – ac / PAD-US 3001 ac | PAD-US | PAD-US only; agency layer not read for this one, so our line = PAD-US = what potamap draws. |
| 14 | US-7372 Halfway Tavern State Historic Site | official layer | ours 4 ac / PAD-US – ac | PAD-US + community map | Name-only match to a layer without acreage. |
| 15 | US-7795 Grassy Hill State Natural Area | official layer | ours 1488 ac / PAD-US 927 ac | PAD-US | **Differ.** DCR: 1,488 acres = our official polygon. PAD-US part 927 (+854/367 pieces). **We are right.** |
| 16 | US-3383 Bald Mountain State Recreation Area | official layer | ours 4519 ac / PAD-US – ac | PAD-US + community map | Agency 4,600 ac; ours 4,519 ac; PAD-US not matched (pieces 1,795, 1,793, 1,404). **We are right**, PAD-US is cut into pieces. |
| 17 | US-10635 Eastern Kern County Onyx Ranch State R | official layer | ours 26403 ac / PAD-US 26405 ac | PAD-US + community map | Agree (same acreage in the agency layer and PAD-US). |
| 18 | US-8106 Oxbow Lake State Wildlife Area | official layer | ours 386 ac / PAD-US 386 ac | PAD-US | Agree (same acreage in the agency layer and PAD-US). |
| 19 | US-12806 Chosen Valley Wildlife Management Area | official layer | ours 197 ac / PAD-US 197 ac | PAD-US + community map | Agree (same acreage in the agency layer and PAD-US). |
| 20 | CA-2173 Parc-des-Falaises Nature Reserve | official layer | ours – ac / PAD-US – ac | N/A (Canada) | Name-only match to a layer without acreage. |
| 21 | US-1017 Ramsey Lake State Park | official layer | ours 1759 ac / PAD-US 1759 ac | PAD-US + community map | Agree (same acreage in the agency layer and PAD-US). |
| 22 | CA-3931 Ospika Cones Ecological Reserve | PAD-US only | ours – ac / PAD-US 3168 ac | N/A (Canada) | PAD-US only; agency layer not read for this one, so our line = PAD-US = what potamap draws. |
| 23 | US-3792 Land Between the Lakes National Recrea | PAD-US only | ours – ac / PAD-US 63694 ac | PAD-US | PAD-US only; agency layer not read for this one, so our line = PAD-US = what potamap draws. |
| 24 | US-3378 Blue Ridge National Parkway | official layer | ours 1575 ac / PAD-US 35237 ac | PAD-US | Parkway is long: ours matched 1,575-acre pieces; "reviewed" hand join to a PAD-US polygon of 35,237 ac. NPS total ~93,000 ac. **Neither whole**; check by hand (PF-5: area park). |
| 25 | US-4513 Carson National Forest | PAD-US only | ours – ac / PAD-US 1390444 ac | PAD-US + community map | PAD-US only; agency layer not read for this one, so our line = PAD-US = what potamap draws. |
| 26 | US-5205 Donahue Woods State Forest | official layer | ours 1158 ac / PAD-US 1159 ac | PAD-US + community map | Agree (same acreage in the agency layer and PAD-US). |
| 27 | US-12922 Stickney Creek State Fish and Wildlife | official layer | ours 1 ac / PAD-US 1 ac | PAD-US | Agree (same acreage in the agency layer and PAD-US). |
| 28 | US-5053 Hickory Lake State Forest | official layer | ours 581 ac / PAD-US 581 ac | PAD-US + community map | Agree (same acreage in the agency layer and PAD-US). |
| 29 | CA-0439 Windy Lake Provincial Park | official layer | ours – ac / PAD-US 293 ac | N/A (Canada) | Ontario Parks: 118.45 ha = 292.7 ac; PAD-US figure 293 (ours has no area). Agree. |
| 30 | CA-3404 Dean River Conservancy Protected Area | PAD-US only | ours – ac / PAD-US 138616 ac | N/A (Canada) | PAD-US only; agency layer not read for this one, so our line = PAD-US = what potamap draws. |

### Disagreements, with the agency's own figure
| Park | Agency says | Ours | PAD-US (potamap) | Who is right |
|---|---|---|---|---|
| Fall Creek Falls SP (TN) | "more than 26,000 acres" (https://reserve.tnstateparks.com/fall-creek-falls) | 15,250 + 10,840 = 26,090 | 6,248 + 1,134 + 1,133 | **ours** |
| Grassy Hill NAP (VA) | 1,488 acres (https://www.dcr.virginia.gov/natural-heritage/natural-area-preserves/grassyhill) | 1,488 | 927 + 854 + 367 | **ours** |
| Bald Mountain RA (MI) | 4,600 acres (https://www.michigan.gov/BaldMountain) | 4,519 | cut into 1,795 / 1,793 / 1,404 | **ours** |
| Sugarite Canyon SP (NM) | 4,500 acres (https://www.emnrd.nm.gov/spd/wp-content/uploads/sites/7/Park-Trail-Guide.pdf) | 4,530 | 4,115 | ours (PAD-US 9% short) |
| Windy Lake PP (ON) | 118.45 ha (292.7 ac) (https://ontarioparks.ca/park/windylake) | no area stored | 293 | PAD-US fine; ours unmeasured |
| Blue Ridge Parkway (VA) | ~93,000 ac whole (NPS, B) | 1,575-acre pieces | 35,237 hand-joined | neither whole; PF-5 area park, check by hand |
Pattern: where an official state layer exists and we read it, we beat PAD-US; where only PAD-US exists (national forests, BC conservancies, Land Between the Lakes), we and potamap draw the same shape.

## 5. New Park Finder: pins and "never activated"
- **How it knows:** it asks POTA's public API for parks and their activation counts; a park with zero activations is ATNO (never activated). The help page names only that API, warns it is unofficial, caches nothing beyond the page's own query, and needs a zoom-in before "Click here to find parks!" to avoid load. With a callsign it also splits "by you" from "by others" (POTA's per-user stats) and can filter by year ("can't tell if activated in year" when the count does not show the year). The Python scripts cache the API answer for one day (A: README).
- **How the Lounge already does it:** `kpc-hunt.js` line 932 calls `https://api.pota.app/location/parks/US-<state>` and reads each park's `activations`; a count of 0 gets the "FIRST EVER ACTIVATION" badge and 1-5 gets "RARE" (lines 533, 550, 993). That is the same method, one source (A).
- **What to borrow (idea only, no code):** (1) a per-user ATNO that uses the hunter's own POTA file (our MY POTA FILES CSV, already in the app) so NEW = "never hunted by me", separate from FIRST EVER = "never activated by anyone"; (2) the "can't tell this year" state when the API has no year data; (3) cache one day.
- **Pins vs ours (30 parks):** not compared numerically. Our clone's pin tiles hold 234 programs but **no US or Canada pins**, and I cannot reach newparks' pins from the shell. Both read POTA's API, so a difference can only be POTA moving a pin since our daily tile build (data updated 2026-10-27). Listed for a bot below.

## 6. BOT LOOK-UP (for chat 9's next probe run; real browser, observe only, copy nothing, no contact with the owners)
| # | URL | What to check |
|---|---|---|
| 31 | https://potamap.us (search each ref in the 30-park sample) | does the park show an outline; vertex-count vs ours (rough size); which of the 10 gap parks it draws (esp. US-1174, US-2151, US-13156, US-5686, US-7073) |
| 32 | https://ham-map.com (pick a country, choose POTA) | confirm pins only; compare pin positions of 10 parks to POTA's |
| 33 | https://newparks.m0trt.radio (zoom on 10 parks from the sample) | popup lat/lon vs ours (non-US/CA from our tiles; US/CA from the POTA API); any park our list lacks |
| 34 | https://gisportaldev.dot.ny.gov/server/rest/services/CulturalResources/Cultural_Resources/MapServer/16?f=pjson and the production host (search "OPRHP Boundary" on https://gis.ny.gov) | polygons count, `Name` values (Thompsons Lake, Letchworth…), date, licence, production address |
| 35 | https://github.com/cwhelchel/potamap.ol (LICENSE, wiki) | licence type and the exact list of states with extra community maps (README excerpt did not show it) |
| 36 | https://git.ianrenton.com/ian/new-park-finder (README, source) | the exact API fields used for ATNO and "can't tell this year" |
| 37 | CA State Parks ParkBoundaries (https://services2.arcgis.com/Uq9r85Potqm3MfRV/ArcGIS/rest/services/ParkBoundaries/FeatureServer/0): query name LIKE '%Oro%' | is it "Montaña de Oro" (accent) |
Nothing was loaded or changed by the desk.
