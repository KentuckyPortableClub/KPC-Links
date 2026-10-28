# Big holes: official layers (desk, Oct 27 2026, read only)
Grades: A = opened/read, B = search result only, C = inference. Layer NUMBERS (…/MapServer/0) could not be opened from the desk (REST roots are blocked here): a bot must confirm each one before use.

| # | Hole | REST address | Publisher | Date | Licence | Covers | Grade |
|---|------|--------------|-----------|------|---------|--------|-------|
| 1 | **Mississippi WMAs** | https://gis.mississippi.edu/server/rest/services/Administrative/MS_WildlifeManagementAreas_2019/MapServer (318 polygons; fields ID, TYPE, ACREAGE, Name; TYPE incl. WMA, State Park, Lake, Refuge Waterfowl, Dog Hunting Area) | MARIS (Mississippi Automated Resource Information System) from MDWFP | 2019-09-11; a 2026 shapefile exists: https://maris.mississippi.edu/MARISdata/Boundaries/MS_WildlifeManagementAreas_2026.zip (no REST) | metadata says no access/use limitations; MARIS use page https://maris.mississippi.edu/HTML/RESOURCES/Liability.html NOT read | the 20 no-outline WMAs (US-7072..7121); TYPE "Lake"/"State Park" may cover some fishing lakes and Percy Quin: unconfirmed | A (page), C (layer number) |
| 1b | **Mississippi State Parks** | https://gis.mississippi.edu/server/rest/services/Cultural/MS_StateParks_2019/MapServer (53 polygons); 2026 zip https://maris.mississippi.edu/MARISdata/Cultural/MS_StateParks_2026.zip | MARIS | 2019 / 2026 | as above | Percy Quin US-2549, Clark Creek US-9847, maybe the 22 State Recreation Areas | A/C |
| 1c | MS recreation facilities (points) | https://gis.mississippi.edu/server/rest/services/Cultural/MS_RecreationalFacilities_2017/MapServer | MARIS / MDWFP | 2017 | not read | pins for fishing lakes, SRAs | A/C |
| 1d | MS federal | NF ownership …/Environmental/MS_NationalForestOwnership_2017/MapServer; NWR …/Administrative/MS_NationalWildlifeRefuges_1997/MapServer; PAD-US …/Environmental/MS_USGSProtectedAreasData_2021/MapServer | MARIS | 2017 / 1997 / 2021 | as above | Gulf Islands, Emerald Mound (via PAD) | B |
|   | NOTE | MARIS's index page still lists the dead host www.maris.state.ms.us; the live host is **gis.mississippi.edu**. No Corps layer in MARIS. | | | | | |
| 2 | **Michigan state forests** | Not found. The 16 "DNR Forest Management Units" (https://services3.arcgis.com/Jdnp1TjADvSDxMAX/arcgis/rest/services/DNRWILDLandsOPENDATA/FeatureServer/2, fields ForestManagementUnit, UnitManager; edited Oct 2026) do NOT equal the 6 legal state forests (Au Sable, Copper Country, Escanaba River, Lake Superior, Mackinaw, Pere Marquette = US-4774..4779). "DNR Managed Sites" not located (RecLoc MapServer on mcgi.state.mi.us has points only). | Michigan DNR | – | not stated on the DNR page | parks/SRAs already covered by …/DNRManagementBoundariesOPENDATA/FeatureServer/8 | B. **Needs a bot to list the services in that ArcGIS org.** Do not use FMUs as state-forest outlines. |
| 3 | **Indiana DNR properties** | https://gisdata.in.gov/server/rest/services/Hosted/ManagedLands_DNR_Open/FeatureServer/0 (fields unitname, manager, owner, access_, dedicated_, subunit, acres) | Indiana DNR + Natural Heritage + State Land Office (with USDA, DOI, local agencies) | no date shown | not shown; layer says "by no means a complete dataset" | state parks, SRAs, forests, FWA, preserves; already in our key as `ind` | A. Mixes kinds: use `manager` as a per-record kind (see name-match sheet). Also Hosted/Sites_StateParks/FeatureServer/8, NaturePreservesCoastalArea/FeatureServer/0 |
| 4 | **Minnesota WMAs** | https://gis.dnr.state.mn.us/appserver/rest/services/webGDRS/bdry_dnr_wildlife_mgmt_areas_pub/MapServer ; already used: https://enterprise.gisdata.mn.gov/aghost/rest/services/us_mn_state_dnr/bdry_dnr_wildlife_mgmt_areas_pub/FeatureServer/0 | Minnesota DNR | not shown | not shown (MN Geospatial Commons record not opened) | ~1,392 public WMAs, ~1.29 M acres. "Not accurate enough to legally locate boundary lines" | A. Already in key; nothing new to add except the licence check. |
| 5 | **Army Corps project land** | No national fee-land polygon service found. Only: ND https://services1.arcgis.com/GOcSXpzwBHyk2nog/ArcGIS/rest/services/NDGISHUB_Army_Corps_Lands/FeatureServer ; HIFLD "usace_owned_and_operated_reservoirs" (point/reservoir) https://maps.nccs.nasa.gov/mapping/rest/services/hifld_open/water_supply/MapServer/10 ; district/division outlines (not land). | ND GIS Hub; HIFLD | – | – | ND only. Everything else = PAD-US Fee records managed by USACE (B1 rule) | B. **Five states for rule 14 not identified by the desk: chat 2 must name them.** Next try: each Corps district's own open-data hub (Nashville, Louisville, Huntington, Tulsa, Little Rock, Mobile). |
| 6 | **TVA land** | None found. Only reservoir-land-management-plan web pages (tva.com). | TVA | – | – | – | B. Treat as PAD-US Fee (TVA); ask TVA for a data page. |
| 7 | **North Carolina state parks** | None found again. In the key already: NC_Public/Managed_Areas/MapServer/0 (NC Natural Heritage, preserve) and NCWRC gamelands_general/FeatureServer/21. | – | – | – | – | B. NC Parks (ncparks.gov) page "Maps" section + NC OneMap are the next two looks (research order rule 2). |
| 8 | **Manitoba parks** | https://services.arcgis.com/mMUesHYPkXjaFGfS/ArcGIS/rest/services/Manitoba_Parks/FeatureServer/0 (fields NAME_E, TYPE_E, PRK_CLSS, OWNER_E, MGMT_E) | Government of Manitoba, Parks and Protected Spaces Branch | published 2018-01-03; record modified 2025-02-05; data current to June 2017; last edit Nov 14 2021 | **OpenMB Information and Data Use Licence** (https://cti.gov.mb.ca/asset_library/en/legal/OpenMB-Information-Data-Use-Licence.pdf: free use incl. commercial with attribution; full text not read by the desk, B) | 92 provincial parks + 1 park reserve; "not a legal definition". Record: https://open.canada.ca/data/en/dataset/024277ff-9ed5-515b-aa33-7624d932a13d | A (layer), B (licence text) |
| 9 | **PE** | already in key: GeoLinc_Provincial_Parks/MapServer/0 | PEI government | see KPC_CAE_PE_desk.md | see file | provincial parks | no new work |
| 10 | **NT** | see KPC_CAW_NT_desk.md | | | | | not re-researched this round |

## What chat 2 / Brandon must do
1. A bot confirms the MS layer numbers and reads the MARIS use page (items 1, 1b).
2. A bot lists every service in Michigan DNR's ArcGIS org (services3 …/Jdnp1TjADvSDxMAX) to find state forests / "Managed Sites".
3. Chat 2 names the five Corps states; then one Corps-district hub search per state.
4. Manitoba: attribution line required: "Contains information licensed under the OpenMB Information and Data Use Licence."
Nothing was loaded or changed by the desk.

---
# ROUND 2 (desk, Oct 27 2026 night, read only)
Grades: A opened, B search only, C inference. Skipped on purpose: historic sites, markers, city/county parks (pin-only).

## R2-1 Ranking: parks with NO outline (from the region summaries; "real" = after removing hatcheries, historic sites, BLM point parks, municipal)
| Rank | Place | No outline / total | Real gap | What the hole is |
|---|---|---|---|---|
| 1 | NV | 153 / 367 | 103 | 68 markers (never); rest Tahoe name mismatch + rulings: mostly NOT a missing layer |
| 2 | ID | 155 / 361 | 74 | **missing layer**: IDPR state parks (5 SP + 31 SRAs). New lead below |
| 3 | MS | 66 / 155 | 66 | missing layer (see Round 1); 22 SRAs + 15 fishing lakes |
| 4 | OK | 62 / 205 | ~40 | 22+ historic sites (skip); WMAs on Corps/military land = rule 14 |
| 5 | WA | 68 / 536 | 57 | 13 state forests = **name mismatch**; 16 DNR recreation sites = missing layer (lead below) |
| 6 | UT | 333 / 692 | 57 | BLM point parks (pin-only); rest key check |
| 7 | AR | 54 / 304 | 54 | AHTD public land + trails unread; 15 "trails" are scenic byways |
| 8 | ND | 53 / 155 | ~17 | 36 historic sites (skip); State Forests layer is 2011 |
| 9 | OR | 74 / 440 | 51 | 18 hatcheries (skip); ODF forests = add layer |
| 10 | NC | 34 / 253 | 34 | missing layer: state parks (see R2-5) |
| 11 | MN | 36 / 294 | ~20 | Lake Superior MPAs + trails |
| 12 | WY / MT / KS | 100 / 298, 27 / 254, 27 / 145 | 32, 26, ~13 | hatcheries, historic sites: mostly skip |
| 13 | AL 29, VA 29, TN 25, FL 20, GA 17, WV 12, SC 8 | | | mostly **name mismatches** (De Soto SP, Okefenokee SP, etc.), a few historic sites |
| 14 | IN 22, MI 31, WI 22, MO 17, IL 15 | | | IN = 13 lake SRAs (name/kind issue, layer exists); MI = state forests/harbors; rest name mismatches |
Canada: QC 398 (about 230 municipal = skip), NB 256, ON 255 (85 NHS pin-only; rest fuzzy match), NS 168, MB 89, YT 85 (campgrounds pin-only), NL 67 (**licence**: provincial file may not be redistributed), NT 53, PE 36.
Biggest REAL missing-layer holes: ID, MS, WA rec sites, AR, NC, OR forests, NT, PE, NS, MI forests, Corps/TVA.

## R2-2 Michigan state forests (Round 1 stubborn)
- Walked the DNR ArcGIS account (services3 …/Jdnp1TjADvSDxMAX). `DNRManagementBoundariesOPENDATA/FeatureServer` has 10 layers (A): 0 Finance/Operations units, 1 Fisheries units, **2 Forest Management Units (16, "Michigan's nearly 3.9 million acres of State Forest Land")**, 3 Forest District, 4-5 Law Enforcement, 6 Parks District, 7 Wildlife Management Units, **8 Parks Unit Boundary (state parks + State Recreation Areas)**, 9 Trails Management Units. No layer is named for the 6 legal state forests (Au Sable, Copper Country, Escanaba River, Lake Superior, Mackinaw, Pere Marquette = US-4774..4779) and none for State Game Areas or "Managed Sites".
- Other services in the account: `MiStateForest/FeatureServer` (A: inventory; compartments, treatments, "areas unavailable to harvest"; layers 0-6, 8, 9; no state-forest names), `DNRForestInventory/FeatureServer/4` "DNR Forest Inventory - State Land" (B; the polygons of all state forest land; layer page would not open), `Michigan_DNR_Public_Forest_Inventory_Data/FeatureServer`, `DMU_Service`.
- Hub dataset **"Michigan DNR Project Boundary 2020"** (B, OSM wiki): "boundaries for state parks, forest management units, wildlife areas, recreation areas and other property holdings": the best candidate for the old "Managed Sites" idea. Hub page https://gis-midnr.opendata.arcgis.com/datasets/midnr::michigan-dnr-project-boundary-2020/ does not open from the session. Licence not stated anywhere.
- Verdict: **no official polygon for the 6 named state forests found.** FMUs must NOT be used as their outlines (16 units, other names). Fallback = OpenStreetMap outline (unofficial label), or union of State Land compartments per FMU (C, would not match legal names).

## R2-3 Army Corps project land (Round 1 stubborn)
- USACE's own hub **https://geospatial-usace.opendata.arcgis.com/** has datasets (B, titles only; the pages did not show geometry, service URL, fields, licence or date): "USACE Reservoirs: boundary data for Corps owned and operated reservoirs" (/datasets/03e322d7e89b48a9b48e9c3f4bcaf29e_0), "USACE Recreation Areas" (/datasets/e314790ee1bb4eec982f0b669accb6fc_0), "IRM Property Boundary" (= FUDS cleanup sites, NOT fee land; ignore), USACE Regulatory Boundary and district/division outlines (not land).
- Also found (B): NDGISHUB Army Corps Lands https://services1.arcgis.com/GOcSXpzwBHyk2nog/ArcGIS/rest/services/NDGISHUB_Army_Corps_Lands/FeatureServer/0 and second host https://gis.dmr.nd.gov/dmrpublicservices/rest/services/OilGasPublicMapDataVectorTiles/Army_Corps_of_Engineers/FeatureServer/0 (ND only).
- Verdict: no national fee-land polygon found. The Reservoirs and Recreation Areas datasets are the leads; both are on BOT LOOK-UP. Until read, rule 14 keeps using PAD-US Fee records managed by USACE.
- "Five states" for rule 14 still not named to the desk: chat 2 please say which.

## R2-4 TVA land
- Searched again: only TVA web pages (reservoir land management plans, land policy) and generic federal/state layers. **No TVA land polygon service found.** TVA lands remain PAD-US Fee (TVA) records. BOT LOOK-UP: ask whether TVA's open data page or ArcGIS Online account publishes "TVA Land" / "Reservoir Land Management Plan zones" (zones are planning, not the land line).

## R2-5 North Carolina state parks
- Three more searches (NC OneMap, ncparks.gov, data.gov): **nothing official found**; hits were other states' park layers (CA, PA, WV…). Remains: NC Natural Heritage `Managed_Areas/MapServer/0` (already in key, many owners, state parks are inside it by `MATYPE`/name, C) and NCWRC game lands. 34 NC parks stay unmatched; many are probably name-style mismatches against Managed_Areas. BOT LOOK-UP: https://www.ncparks.gov (each park's "Maps" section), NC OneMap catalogue (https://www.nconemap.gov), DNCR ArcGIS Online account.

## R2-6 Northwest Territories (NEW, A)
- **https://www.apps.geomatics.gov.nt.ca/arcgis/rest/services/GNWT/Environment_LCC/MapServer/195** "Federal/Territorial Conservation Areas": polygon, key fields Name, Designation, Status, Protection, Legislation, Size_Km2, Management, Jurisdiction; includes Territorial Protected Areas, national parks and reserves, NWAs, MBSs, Thaidene Nene, Thelon, and "areas of larger Territorial Parks (Territorial Recreation Park, Territorial Natural Environment Park)". Publisher: Conservation Planning and Implementation Unit, ENR, GNWT (metadata 2022). Parent layer 192 "Established Protected/Conservation Areas". Gwich'in Territorial Park updated by NWT Centre for Geomatics from metes and bounds; Thelon boundary has known inaccuracies. Marine protected areas are in a separate class; NWT Wildlife Act game sanctuaries are NOT in it.
- Licence: the NT open data record for Territorial Parks (a tourism points map) says Open Government Licence NWT (https://www.gov.nt.ca/en/open-government-licence-northwest-territories), modified 2026-04-02 (A). The 195 layer's own licence is not stated (C: same publisher, same OGL). Mirror hosts: appstest/sandbox.geomatics.gov.nt.ca (test hosts, do not use).
- Covers: the territorial parks that are in the 53 no-outline NT parks, except campground-style "parks" (points). Cross-check names before loading.

## R2-7 Prince Edward Island
- Still **no open provincial park polygon service** found. The province's GIS data is by download with accepted licence terms (http://www.gov.pe.ca/gis/index.php3?number=77543&lang=E; 'free' with a licence form, B) and a Public Land Atlas (view at www.gov.pe.ca/gis; shows provincial forests, wildlife management areas, provincial and national parks, natural areas; no download or licence stated). PE's REST host exists (https://gis.princeedwardisland.ca/server/rest/services/ with Base_2025/ and Hosted/ folders, B). BOT LOOK-UP: walk that services folder for a parks / public lands layer. Earlier key layer GeoLinc_Provincial_Parks/MapServer/0 stays.

## R2-8 Other new leads (outside the Round 1 list)
- **Idaho IDPR open-data hub (A, hub exists): https://idpr-data-idaho.hub.arcgis.com/** (hub id 6d30d6f7839c4ae3ab14e7dd9c8bdd9b; collections list at https://idpr-data-idaho.hub.arcgis.com/api/search/v1/collections would name the datasets; licence not stated). Likely home of the missing state park and SRA outlines (74 ID holes). BOT LOOK-UP first.
- **Washington DNR recreation sites (B):** https://gis.dnr.wa.gov/site2/rest/services/Public_Recreation/DNR_Recreation_Sites/FeatureServer (also …/Recreation/DNR_Recreation_Sites/MapServer). The session got a sign-in page for the layer list: BOT LOOK-UP (layer ids, polygon or point). Our key uses site3 Public_Boundaries only.

## R2-9 Name mismatch, not missing layer (do not hunt layers for these)
WA 13 state forests; AL De Soto SP, Butler County WMA, Kinterbish WMA; GA Okefenokee SP; NV Tahoe; IN 13 lake SRAs (layer ManagedLands_DNR_Open has them under unit names like "Unit on Lake", see the name-match sheet); ON most of the 255 (fuzzy match); CT RI MA NH ME DE name mismatches; TX 10 historic-site suspects.

## R2-10 BOT LOOK-UP table (for chat 9's next probe run)
| # | URL | What to check |
|---|-----|---------------|
| 1 | https://gis.mississippi.edu/server/rest/services/Administrative/MS_WildlifeManagementAreas_2019/MapServer ; …/Cultural/MS_StateParks_2019/MapServer ; …/Cultural/MS_RecreationalFacilities_2017/MapServer | layer numbers, fields, polygon vs point, count; do TYPE "Lake"/"State Park" rows match Percy Quin, Clark Creek, fishing lakes |
| 2 | https://maris.mississippi.edu/HTML/RESOURCES/Liability.html | use terms |
| 3 | https://gis-midnr.opendata.arcgis.com/datasets/midnr::michigan-dnr-project-boundary-2020/ | service URL, polygons, names (state forests? SGAs?), licence, date |
| 4 | https://services3.arcgis.com/Jdnp1TjADvSDxMAX/ArcGIS/rest/services?f=json | full service list of the Michigan DNR account (look for "State Forest", "Managed", "Project Boundary") |
| 5 | https://services3.arcgis.com/Jdnp1TjADvSDxMAX/ArcGIS/rest/services/DNRForestInventory/FeatureServer/4 | does it carry a state forest name field |
| 6 | https://geospatial-usace.opendata.arcgis.com/datasets/03e322d7e89b48a9b48e9c3f4bcaf29e_0/about and …/e314790ee1bb4eec982f0b669accb6fc_0/about | service URL, geometry, fields, date, licence, whether it is fee land or lake outline; then each Corps district hub |
| 7 | https://www.tva.com (search "GIS", "open data", "land data") and https://www.arcgis.com/home/search.html?q=owner%3ATVA | any TVA land layer |
| 8 | https://www.ncparks.gov (one park's Maps section) ; https://www.nconemap.gov | state park boundary layer or download |
| 9 | https://www.apps.geomatics.gov.nt.ca/arcgis/rest/services/GNWT/Environment_LCC/MapServer/195?f=pjson | confirm polygon count, which names are territorial parks, licence text |
| 10 | https://gis.princeedwardisland.ca/server/rest/services/?f=json (walk Hosted/ and other folders) ; http://www.gov.pe.ca/gis/index.php3?number=77543&lang=E | parks / public land layer, licence terms |
| 11 | https://idpr-data-idaho.hub.arcgis.com/api/search/v1/collections | names of IDPR datasets; park boundary service URL; licence |
| 12 | https://gis.dnr.wa.gov/site2/rest/services/Public_Recreation/DNR_Recreation_Sites/FeatureServer/layers | layer ids, polygon or point |
| 13 | https://enterprise.gisdata.mn.gov (MN Geospatial Commons record for DNR WMAs) | licence and date for the WMA layer |
Nothing was loaded or changed by the desk.

---
# ROUND 3: the West is federal land (desk, Oct 27 2026 night, read only)
Method: for NV, ID, UT, OR, WA I took every POTA park with NO match in `data/us-key/US-XX.json` (783 parks) and sorted them by POTA's own park type (A: the data). Layers the key already reads come from `data/us-key/layers.json` (A). Layer facts are from the REST pages named (A where "opened", B where search only).

## R3-1 What kind are the 783 missing western parks?
| Kind (POTA type) | Count | NV | ID | UT | OR | WA | Is it an outline problem? |
|---|---|---|---|---|---|---|---|
| BLM "Recreation Management Area" / "Special RMA" | 347 | 11 | 76 | 230 | 19 | 11 | **Mostly single SITES, not areas** (boat ramps, trailheads, kiosks, springs, caves, access points: e.g. "Swaseys Boat Ramp", "Red Reef Trail", "Portneuf Gap River Access", "Pipeline Recreation Site"). A rough name test says about 200 of 347 are site-like. These are POINTS: pin-only. Some are true areas (Klamath Hills, Leslie Gulch, Diamond Craters, Logandale Trails, Dry Valley SRMA, Cathedral Valley Scenic Backway): those are likely name mismatches against the polygon layers we already read (C, bot check) |
| State rec sites / parks / forests | 136 | 9 | 45 | 14 | 29 | 39 | State layers: IDPR (36), WA DNR rec sites (16) + 13 forests (name mismatch), OR (hatcheries skip, ODF forests): see Round 2 |
| Historic (State Historical Monument etc.) | 96 | 80 | 3 | 9 | 2 | 2 | skip (markers, never) |
| BLM historic / interpretive sites | 51 | 16 | 4 | 29 | 2 | | points: pin-only |
| BLM backcountry airstrips | 27 | 21 | | 6 | | | points: pin-only |
| National Historic / Scenic / Geologic trails | 29 | 3 | 7 | 7 | 7 | 5 | **lines** (see R3-3): one national layer covers them |
| Scenic byways / "National Parkway" / Outstanding Natural Beauty | 24 | 10 | 7 | 6 | | 1 | roads: not parks, skip or pin-only (Utah's POTA calls them "National Parkway") |
| Wild & Scenic Rivers (BLM and Forest Service) | 24 | | 5 | 7 | 9 | 3 | corridors/lines: layers exist (R3-2) |
| Federal areas (monument, NRA, wilderness, herd area) | 19 | 1 | 2 | 9 | 3 | 4 | polygons: layers are read; most are name mismatches (e.g. Hanford Reach NM, Mt St Helens NM, Newberry NM: Forest Service/FWS units) |
| National Forest | 6 | | | 3 | | 3 | name mismatch ("La Sal Mountain" = Manti-La Sal; "Columbia River Gorge National Forest" = the Scenic Area; Sawtooth/Caribou-Targhee/Idaho Panhandle listed under the wrong state) |
| Other (WMA 5, scenic sites 3, rec trails 3, rest ~12) | ~35 | | | | | | single checks |

Answer to HQ: **no single national layer closes hundreds of western parks.** About 350 BLM entries are sites (points); the BLM national site-points layer gives their location, not an outline. The areas among them are already covered by the BLM polygon layers the key reads, so the rest is name matching. The real polygon gains from national layers are small: about 24 rivers, 29 trails, and a handful of Forest Service units.

## R3-2 National layers: does the key read them?
| Layer | Address | Geometry | Key reads it? | Would close |
|---|---|---|---|---|
| BLM Recreation Areas (SRMA/ERMA) | https://gis.blm.gov/arcgis/rest/services/recreation/BLM_Natl_Recreation/MapServer/9 (`rma`) and …/BLM_Natl_Recs_poly/MapServer/0 (`rst`) | polygon | **YES (both)** | the true BLM rec areas; misses = name matching |
| BLM Natl Recreation Sites | https://gis.blm.gov/arcgis/rest/services/recreation/BLM_Natl_Recreation/MapServer/3 (A: point; FET_NAME, FET_TYPE 1-14, UNIT_NAME, ADMIN_ST; "interim subset", BLM HQ) ; also …/BLM_Natl_Recs_pts/MapServer (24 point layers: boat ramp, trail head, landing strip, interpretive site, campground, overlook…; A) | point | **NO** | pins (not outlines) for ~350 sites + 51 interpretive + 27 airstrips. Use the FET_NAME, UNIT_NAME fields to confirm names and give a verified pin. Good name-mismatch tool |
| BLM NLCS National Monuments / NCAs | …/lands/BLM_Natl_NLCS_NM_NCA_poly/MapServer/0 (`nca`) | polygon | YES | |
| BLM Wilderness and WSAs | …/lands/BLM_Natl_NLCS_WLD_WSA/MapServer/0 and /1 (`wbl`, `wsa`) | polygon | YES | |
| BLM Wild and Scenic Rivers | https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_NLCS_WSR/MapServer/0 (A: polyline, name field NLCS_NAME; plus table /1 nlcs_desc). Also state: …/utarcgis/…/BLM_UT_WSR/MapServer (B) | line | **NO** | the 7 UT + 1 ID + 1 OR "BLM Wild and Scenic River" parks as line features (lines = 100 ft rule, not polygon) |
| Forest Service Wild and Scenic Rivers | https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_WildScenicRiver_01/MapServer/0 (A: polygon; copyright USFS Enterprise Map Services Program; no date shown) | polygon | **NO** (key reads NPS `wsrc` and the FS wilderness `wld` only) | most of the 24 "National Wild and Scenic River" parks (Salmon, St Joe, Crooked, Grande Ronde, Donner und Blitzen, White Salmon, Wallowa…) |
| Forest Service national forest boundaries | https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_ForestSystemBoundaries_01/MapServer (B, layers not opened) | polygon | **NO** (PAD-US covers NFs; the 6 misses are name mismatches) | 6 |
| Forest Service other national designated areas (monuments, NRAs, scenic areas) | https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_OtherNationalDesignatedArea_01/MapServer/0 (B) | polygon | **NO** | Newberry NM, Mt St Helens NM, Columbia River Gorge NSA, NRAs (about 10 across the five states) |
| Forest Service recreation opportunities | https://apps.fs.usda.gov/ArcX/rest/services/EDW/EDW_RecreationOpportunities_01/MapServer/0 (A: point, RECAREANAME) | point | NO | pins for FS recreation sites |
| BLM wild horse herd areas | `hma`, `hab` | polygon | YES | |
| National Historic / Scenic Trails | no BLM or FS national layer opened. NPS trail records are on data.gov (California NHT, Oregon NHT, Pony Express NHT, B: https://catalog.data.gov/dataset/california-national-historic-trail, …/oregon-national-historic-trail, …/pony-express-national-historic-trail); the key reads only `akht` (Ala Kahakai) | line | **NO** | the 29 trail parks (Oregon, California, Pony Express, Lewis and Clark, Nez Perce, Old Spanish, Mormon Pioneer, Transcontinental Railroad) |
| PAD-US | already the base (numeric ids in the key) | polygon | YES | these parks are the ones PAD-US did not match either |

Rule check (house rules): trails, rivers and byways are LINES (100-ft rule); BLM sites are points: they should not be given polygons. "BLM Recreation Management Area" in POTA often names a SITE: say "pin only" on the page, not "no outline".

## R3-3 What to add, in order of payoff (for chat 2 / Brandon)
1. **Forest Service Wild and Scenic Rivers (EDW_WildScenicRiver_01/0) + BLM NLCS WSR lines**: about 24 parks, official. Two layers, one batch.
2. **Forest Service other national designated areas** (about 10 monuments/NRAs/scenic areas): one layer.
3. **BLM Natl Recreation Sites (points, layer 3)** as a name-and-pin source for the ~350 site-type entries; no outlines promised.
4. **National Historic Trails** (29): NPS trail lines; needs a service address from a bot (data.gov records not opened).
5. Name-matching pass for the BLM areas the key already reads (Leslie Gulch, Klamath Hills, Diamond Craters, Logandale Trails, Cathedral Valley, Dry Valley…): the polygon layers hold them under other names (BLM drops the words "BLM Recreation Management Area"; POTA adds them). A bot can strip that suffix and retry before any new layer is added.

## R3-4 BOT LOOK-UP (Round 3)
| # | URL | What to check |
|---|-----|---------------|
| 14 | https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_WildScenicRiver_01/MapServer/0?f=pjson | fields (name), count, licence note, whether names match POTA ("Salmon", "St Joe", "Grande Ronde"…) |
| 15 | https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_OtherNationalDesignatedArea_01/MapServer/0?f=pjson | designation values (National Monument, NRA, Scenic Area), names |
| 16 | https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_ForestSystemBoundaries_01/MapServer?f=pjson | layer ids; confirm Manti-La Sal, Columbia River Gorge, Umatilla, Idaho Panhandle names |
| 17 | https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_NLCS_WSR/MapServer/0?f=pjson | field list, count in UT/ID/OR |
| 18 | https://gis.blm.gov/arcgis/rest/services/recreation/BLM_Natl_Recreation/MapServer/3 | run name query with the 347 POTA names (suffix stripped) on FET_NAME / UNIT_NAME; report hit rate by FET_TYPE |
| 19 | https://gis.blm.gov/arcgis/rest/services/recreation/BLM_Natl_Recs_poly/MapServer/0 and …/BLM_Natl_Recreation/MapServer/9 | same name query with the suffix stripped on the polygon layers: how many of the "true area" names (Leslie Gulch, Klamath Hills…) then match |
| 20 | https://catalog.data.gov/dataset/oregon-national-historic-trail (and California, Pony Express, Lewis and Clark, Nez Perce, Old Spanish, Mormon Pioneer) | the REST/download link of the NPS trail line layer; licence |
| 21 | https://gis.blm.gov/utarcgis/rest/services/NLCS/BLM_UT_WSR/MapServer | Utah's own WSR layer if the national one lacks UT segments |
Nothing was loaded or changed by the desk.
