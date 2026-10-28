# Backup river / shoreline GIS for the water checks (desk, Oct 28 2026)
Question: USGS NHD High Resolution server was down for tonight's KY run. Where else can the WATER'S EDGE (area polygons, not just centerlines) come from?
Grades: A = I opened the address and read it; B = search result only; C = my inference. "Answers now" = the research tool's fetch (could be a cached copy up to 15 min old; my shell has no network, so chat 2/bots must retest from the runner).

## Ranked, best backup first
| # | Source | Address | What it holds | Publisher / date / licence | Answers now |
|---|---|---|---|---|---|
| 1 | **Saved copy of NHDPlus HR (same data as the live map)**: USGS National Map downloads, one zipped file-geodatabase per 4-digit unit (HU4), layers NHDArea + NHDWaterbody + NHDFlowline. KY/OH need about 0514 (Ohio River), 0513, 0512, 0602-0604 (Tennessee/Cumberland), 0710 (Mississippi, Missouri-Illinois side) and neighbours. | https://www.usgs.gov/national-hydrography/nhdplus-high-resolution (A) → The National Map Downloader https://apps.nationalmap.gov/downloader ; files sit on the prd-tnm S3 bucket under StagedProducts/Hydrography/NHDPlusHR (B; confirm the exact path from the downloader, I could not open it) | Full water polygons (NHDArea = wide rivers, NHDWaterbody = lakes). USGS, built from NHD HR at 1:24,000 or better; initial 2018-2021, region reprocessing 2022-23; production paused for 3DHP (A). Licence: not stated on that page; USGS products are normally public domain (C, check the metadata). | Page: yes (A). Download files: not tested |
| 2 | **Same layers, a second USGS door**: the live NHDPlus_HR map server (the one that was down) | https://hydro.nationalmap.gov/arcgis/rest/services/NHDPlus_HR/MapServer ; layers 8 NHDArea, 9 NHDWaterbody, 3/4 flowlines (A) | "Data refreshed October, 2022" (A) | Answered when I opened it (A). Older sibling: https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer (B) | Yes at 00:3x CDT |
| 3 | **Corps Inland Electronic Navigation Charts (IENC)**: river-area and shoreline for the NAVIGABLE rivers (Ohio, Tennessee, Cumberland, Green, Mississippi) | Lines: https://ienccloud.us/arcgis/rest/services/IENC_Feature_Classes/COASTLINE_LINE/MapServer (A, "the line where shore and water meet", WGS84, extent -96.7..-79.5 / 29.7..45.1). Area layer: same host, folder IENC_Feature_Classes, look for a river-area / lake-area class (a HIFLD mirror calls it river_areas_usace_ienc, B; that mirror's robots file blocked me) | Real water's edge along the channels our test pairs sit on. Publisher: USACE IENC (A). No date on the page; Corps publishes in cycles. Licence: federal, public (C) | Yes (A) |
| 4 | **EPA NHDPlus V2.1 on ArcGIS Online** (older, coarser, but a different server) | https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/NHDPlusV21/FeatureServer : layers 1 Waterbodies, 2 Flowlines (A) | Lakes and wide rivers as polygons at medium scale. EPA + USGS, hosted by Esri, published 13 Mar 2019 (A). Public. | Yes (A) |
| 5 | **Census TIGER AreaWater** (county files) | catalog.data.gov "TIGER/Line Shapefile 2023, County, <name>, Area Hydrography" (B) ; census.gov download | Big rivers and lakes as polygons, rough (about 1:100k look), every county, every year. Public domain (B). | Not tested; static files, so rarely down |
| 6 | **Tennessee state base map** | https://tnmap.tn.gov/arcgis/rest/services/ENVIRONMENTAL/HYDRO_FEATURES/MapServer (A) ; layer 1 = WATERBODIES (B) | Statewide hydro lines + polygons from the TN Base Mapping program, 2000-2006, State Plane feet (WKID 2274). State of Tennessee (A). Old. | Yes (A) |
| 7 | **Kentucky DGI** | https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_Rivers_WGS84WM/MapServer (A) | ONE layer, "Rivers", from the 100K NHD. Copyright DGI. No date. Lines/old scale: NOT a good water's-edge source (A). Other KY services (Ky_HydroFlowData, Ky_Stream_Reach_Drainage_Polygons) are flow/catchment, not shorelines (B). | Yes (A) |
| 8 | **NOAA shoreline (CUSP)** | https://services2.arcgis.com/okXm0pb6aWH6XOGI/ArcGIS/rest/services/NOAA_CUSP/FeatureServer (B) | COAST shoreline only; it does not cover the Ohio, Tennessee, Cumberland or Green rivers. Use only for the lower Mississippi delta area, not for our pairs (C). | Not tested |
| 9 | **Ohio EPA hydrography** | https://geo.epa.ohio.gov/arcgis/rest/services/hydro/Hydrography/MapServer (A) | Only 2 line layers: Lake Erie divide and "Major Rivers". No polygons. Not a backup. (A) | Yes |

## What I could NOT find
- TVA Kentucky Lake / Lake Barkley shoreline: no open TVA or Corps (Nashville District) reservoir-shoreline service turned up in search. Barkley is a Corps lake, Kentucky Lake is TVA. Treat as NOT FOUND (B). Rows 1-3 draw both lakes' edge anyway (NHDWaterbody / IENC).
- Ohio state: no statewide Ohio hydrography polygon service found (OGRIP/ODOT results were counties and DOT only, B).
- Kentucky "KyFromAbove" has elevation/imagery, not a water-polygon layer that I could confirm (B).

## Recommendation for chat 2
1. Main plan: save NHDPlus HR (row 1) for the HU4 units that cover KY and OH, keep only NHDArea + NHDWaterbody + NHDFlowline near the candidate spots, store the small cut in the bundle with its date (rule 13). This is the same data as the live map, so answers do not change.
2. Live order: row 2 (live) → saved copy → row 3 (IENC, navigable rivers only) → row 4 → NOT SURE.
3. Mismatch rule: if a second source disagrees with NHD on "is this point in water", do not guess; NOT SURE (rule 14 spirit).
4. A BOT should test rows 1, 3, 4 from the runner and report which answer. I can only vouch for what the research tool opened.

## Runner retest (chat 2, Oct 28 ~00:45 CDT, GitHub runner, test box = Paducah where the Ohio + Tennessee meet)
| # | Result |
|---|---|
| 1 | **Answers.** TNM API lists NHDPlus HR per HU4 (0514 published 2018-08-13); files on prd-tnm S3 `StagedProducts/Hydrography/NHDPlusHR/VPU/Current/GDB|GPKG/NHDPLUS_H_<HU4>_HU4_*.zip` download fine, but are BIG (0514 = 504 MB GDB / 926 MB GPKG). Too heavy for every night; usable as a one-time seed. |
| 2 | **Answers** (live NHDPlus_HR: layer 8 NHDArea 4 features, layer 9 NHDWaterbody 373, 1-5 s; the older `nhd/MapServer` answers too). |
| 3 | **Answers.** Corps IENC (ienccloud.us, 100 classes): DEPTH_AREA (16 at Paducah), COASTLINE_LINE (16), LAKE_AREA (12), LAND_AREA (35); RIVERS_AREA / RIVERS_LINE exist (not counted). Navigable channels only. |
| 4 | **Answers** (EPA NHDPlus V2.1 on AGOL: layer 1 waterbodies 36, layer 2 flowlines 92, 0.1-0.2 s). |
| 5 | **Answers** (Census TIGER: county AREAWATER zip 2024 = 417 KB; TIGERweb Hydro layer 1 Areal Hydrography 178 at Paducah). |
Built (Oct 28): the bot now keeps its own saved copy of the live tiles near every spot (water-<tag>.tar.gz, each tile dated, rule 13): live → saved copy → NOT SURE. Rows 3-5 are NOT wired in (different data = different edges; chat 8 rule 3: a second source never decides alone). If the live map AND the saved copy are both missing, the S3 HU4 file (row 1, same data as live) is the next thing to add.
