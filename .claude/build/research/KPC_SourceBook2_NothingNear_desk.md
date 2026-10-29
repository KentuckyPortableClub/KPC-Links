# Source Book 2: the "nothing near" states (chat 8, Oct 29 ~11:15 AM) — what layer would give these parks an outline
Goal (Brandon 10:29 AM): take Fable's item 1 off his list. Counts = parks with NO outline in the US key today (KPC-Data data/us-key). Boundaries + own-land only, no OSM. Grades: **A** I opened it, **B** a catalog/search page showed it, **C** by pattern, a bot must probe. Park-number lists are in `/data/us-key/US-XX.json` (parks with no `m`/`c`); examples below.

## THE BIG WIN: one national BLM source covers most of the list
The largest 'nothing near' group everywhere is **BLM Recreation Management Areas / Special RMAs / interpretive + historic sites**: UT 228 of 325, ID 71 of 144, NV 20+ of 147, WY 41 of 87, OR 17, WA 11, AK 11. They are not in PAD-US as separate records.
| Layer | What | Link | Grade |
|---|---|---|---|
| **BLM Natl Recreation Site Polygons** | polygons: campgrounds, OHV areas, recreation management areas, natural areas; public domain, updated Oct 13 2026 | FeatureServer `https://services1.arcgis.com/KbxwQRRfWyEYLgp4/arcgis/rest/services/BLM_Natl_Recreation_Site_Polygons/FeatureServer/2`; Hub `gbp-blm-egis.hub.arcgis.com/datasets/BLM-EGIS::blm-natl-recreation-site-polygons` | B (catalog page opened; I could not query it: a bot checks Nevada / Utah / Idaho / Wyoming names) |
| BLM state RMA layers | CA `gis.blm.gov/caarcgis/rest/services/Recreation/BLM_CA_RMA/FeatureServer/0`; AZ `.../azarcgis/rest/services/recreation/BLM_AZ_RECS/FeatureServer/1`; OR `.../orarcgis/rest/services/Facility/BLM_OR_Recreation_Site/MapServer/19`; ID 'BLM ID Recreation Areas Poly' (data.amerigeoss.org) | pattern `gis.blm.gov/<st>arcgis/rest/services` | B for CA / AZ / OR / ID, **C for NV, UT, WY** (probe `/nvarcgis`, `/utarcgis`, `/wyarcgis`) |
| BLM NLCS NV (national monuments, NCAs, WSAs) | polygons for Smoke Creek NCA etc. | catalog.data.gov 'BLM NV NLCS Nevada National Monuments National Conservation Areas and Similar Designations Polygons' | B |
| BLM herd management areas | East Pershing Complex HMA (NV) | BLM national HMA layer (search 'BLM Natl Wild Horse and Burro HMA'); | C |
Hard parts: the BLM names in POTA ("Moon Rocks BLM Recreation Management Area") end with the BLM type word; the layer's `ADMIN_UNIT_NAME`/SRMA name is the match (strip the word). The 21 **BLM Backcountry Airstrips** (NV) and the **historic markers** are points: **pin only** (no polygon exists).

## NEVADA (147 none): 65 State Historical Monuments, 21 BLM airstrips, 10 RMAs, 9 historic preservation sites, 9 Areas of Outstanding Natural Beauty, 5 NHS, 4 BLM historic areas, 4 fish hatcheries…
- **State Historical Monuments (65, e.g. US-13274 Empire & Carson River Mills, US-13276 West End of Hastings Cutoff):** these are roadside markers in the Nevada State Historic Preservation Office program: **no boundary exists; pin only** (grade C, by the name; check one against nvshpo.org).
- **BLM RMAs / historic preservation / interpretive / HMA / NCA (about 35):** BLM sources above (US-12817 Moon Rocks, US-13058 Wilson Canyon, US-13010 Dry Valley SRMA, US-13040 Grimes Point/Hidden Cave, US-13020 Smoke Creek NCA, US-10851 East Pershing HMA).
- **Areas of Outstanding Natural Beauty (9, US-13260 Angel Lake Road, US-13261 Baker Road):** scenic road corridors: no polygon; pin only.
- **State wildlife area US-13023 Artesia Lake:** Nevada Dept of Wildlife layer `sgnva` is already read (17 records): ask chat 2 to retry the name 'Artesia Lake' (maybe a spelling alias). **State park US-4438 Buckland Station:** NV State Parks layers `sgnvb/d/e` are read: a name-match miss, alias candidate.
- **State hatcheries (4):** points; pin only. **Historic districts (Virginia City, Carson City):** city / NPS NHL district layers: NPS 'National Historic Landmarks' boundaries (C).

## MISSISSIPPI (54 none): 22 State Recreation Areas, 15 State Fishing Lakes, 10 WMAs, 2 state historic sites, Gulf Islands NS, Emerald Mound…
- **MARIS `MS_StateParks_2026` (A, page opened):** polygons 'boundaries of the State Parks of Mississippi' from MDWFP, shapefile `https://maris.mississippi.edu/MARISdata/Cultural/MS_StateParks_2026.zip` (2019 REST copy: `https://gis.mississippi.edu/server/rest/services/Cultural/MS_StateParks_2019/MapServer`). Our key lists this layer as 'zip, not a map query': **it only needs a download-and-read step (chat 2 / a bot), not a new source.** Terms: MARIS Liability page (https://maris.mississippi.edu/HTML/RESOURCES/Liability.html), no explicit licence on the page → grade B for terms.
- **MARIS `MS_WildlifeManagementAreas_2019` (B, metadata PDF in search):** `https://maris.mississippi.edu/METAdata/METAdata_Boundaries/MS_WildlifeManagementAreas_2019_meta.pdf` → data `https://maris.mississippi.edu/MARISdata/Boundaries/MS_WildlifeManagementAreas_2019.zip` (pattern C) and a REST copy under `gis.mississippi.edu/server/rest/services/Boundaries/` (C). Covers the 10 WMAs (US-7072 Riverfront, US-7097 Chickasaw…).
- **State Fishing Lakes (15, e.g. US-12193 Lake Claude Bennett):** MDWFP lakes are small ponds; probably in `MS_RecreationalFacilities_2017` (points) or MDWFP's lake pages. **Pin only until a polygon is found.**
- **Gulf Islands NS (US-0661):** NPS boundary (national NPS boundaries layer is already used for other parks: why none? a name-match miss: check 'Gulf Islands'). **Emerald Mound, Natchez, Dancing Rabbit Creek (state/federal historic sites):** NPS / state: points or small tracts; pin.
- Past dead ends (chat 9): `maris.state.ms.us` no DNS, `mdwfp.com` SSL fails: use maris.mississippi.edu.

## NORTH DAKOTA (50 none): 36 State Historic Sites, 5 Wetland Management Districts, 5 State Forests, 2 national trails…
- **State Historic Sites (36, e.g. US-12782 Camp Arnold, US-12783 Camp Corning):** State Historical Society of ND sites; no polygon layer found: **pin only** (C).
- **State Forests (5, US-5741 Turtle Mountain, US-5743 Mouse River):** ND GIS Hub 'State Forests' (B): the AmeriGEOSS page shows **tabular data only (CSV, no geometry, last data update 2017)**, CC-BY: `https://gishubdata.nd.gov/sites/default/files/NDHUB.StateForest.csv`. The ND Hub also serves a MapServer 'ND_State_Forest' at `gis.dmr.nd.gov/dmrpublicservices/rest/services/OilGasPublicMapDataVectorTiles/ND_State_Forest/MapServer/0` (B: the title suggests polygons, an oil-and-gas map copy: probe it). If it carries polygons, that gives all 5.
- **Wetland Management Districts (5, US-0421 Arrowwood, US-0425 Devils Lake…):** a WMD is an administrative district of many small waterfowl production areas, not one outline: **FWS National Realty boundaries** (`https://catalog.data.gov/dataset/fws-national-realty-boundaries`, B) give the individual tracts; the district itself has NO single outline. Recommend pin only, or the tracts as a multi-part outline (chat 2 + Brandon's call: grey).
- **International Peace Garden (US-7143):** a private/international park on the border: pin. **Missouri River State Natural Area (US-8561):** ND Parks layer `sgndb/c` is read: alias candidate.
- **North Country NST / Lewis and Clark NHT:** NPS trails (lines): `https://mapservices.nps.gov/arcgis/rest/services/NationalDatasets/NPS_Public_Trails/FeatureServer/0` (B) + national historic trail lines in the NPS Trails layer; trails are lines (R: 100 ft).

## NEXT STATES BY COUNT (what layer type fixes most)
| State (none) | Biggest groups | Source |
|---|---|---|
| **UT 325** | 228 BLM RMAs / SRMAs / historic / interpretive; 6 parkways; 6 national historic trails | BLM Natl Recreation Site Polygons + Utah's own `gis.blm.gov/utarcgis` (C); NPS Trails for the historic trails and parkways |
| **ID 144** | 71 BLM RMAs, **31 State Recreation Areas**, 5 state parks, 7 national parkways | BLM ID Recreation Areas Poly (B); Idaho Dept of Parks and Recreation open data (Idaho Geospatial Gateway / INSIDE Idaho; B-C: bot probe) |
| **WY 87** | 41 BLM, 7 state fish hatcheries (points), 5 national historic trails, 3 battlefields | BLM + NPS; hatcheries = pin only |
| **OR 59** | 12 state fish hatcheries (points), 17 BLM, 5 wild and scenic rivers | OR BLM Recreation_Site layer 19 (B); USFS/NPS Wild & Scenic River lines (chat 9 found R2/R5 = 249 river lines, NPS NRI 4,496 lines) |
| OK 57 | 17 State Historic Sites + 5 Historic Sites, 5 state fishing lakes | Oklahoma Historical Society (no polygons known: pin), OK Wildlife Dept lakes (C) |
| AR 52 | 15 State Trails, 9 State Recreation Areas, 4 NHT | Arkansas GIS Office open data (B: gis.arkansas.gov) + NPS Trails |
| WA 49 | 12 State Forests (DNR), 11 BLM, 4 recreation sites | WA DNR 'state forest' layer (open data B); BLM |
| AK 40 | 11 BLM, 9 NPS wild & scenic rivers, 7 state recreation sites | Alaska DNR Parks open data (C); BLM |

## What this means for Fable's list
1. **Three national layers fix more than state hunting does:** BLM recreation polygons (about 400 of the 'nothing near' parks), NPS trails + NRI/WSR river lines (about 60), FWS realty boundaries (the refuge units).
2. **Two real shortcuts:** MS State Parks and MS WMAs are **already on MARIS as downloads** (just not a map query): 32 parks. ND State Forests: probe the `ND_State_Forest` MapServer (5 parks).
3. **Pin-only by nature (no polygon exists, do not keep hunting):** historical markers (NV 65), airstrips (21), scenic road areas (9), state fish hatcheries (about 30 US-wide), most state historic sites (ND 36, OK 22). Mark them 'pin only: no boundary exists' so nobody re-hunts them.
4. **Bot hand-off (chat 9 / a runner, NET open):** (a) query BLM Natl Recreation Site Polygons for NV UT ID WY OR WA AK names; (b) probe `gis.blm.gov/{nv,ut,wy}arcgis/rest/services`; (c) download MARIS State Parks 2026 + WMAs and read names; (d) probe ND_State_Forest MapServer; (e) probe the Idaho / WA DNR / Arkansas / Alaska portals listed. Chat 2 reads the layers in; chat 11 checks the matches. I opened only catalog pages from here (no REST queries), so every polygon claim is grade B until a bot confirms.
