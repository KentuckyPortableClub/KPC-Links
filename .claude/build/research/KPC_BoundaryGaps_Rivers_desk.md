# BOUNDARY GAPS + OFFICIAL RIVER LAYERS (Research desk, chat 8, Wed Oct 28 2026)

Rules kept: official sources, free, no key/login. Grades: **A** = opened / our own files, **B** = service or catalog page seen in a search result (not opened), **C** = named from knowledge. I cannot download or test-query from my session, so every "snag" is a BOT LOOK-UP row for chat 9 (probe) / chat 2 (line). Nothing in the repo was changed.

## 1. What US boundaries we lack (A: scoreboard.json, Oct 28)
US missing = **918** of the 1,459 North America total (51 states/DC). Where it sits:
| Type | Missing | Where |
|---|---|---|
| BLM Recreation Mgmt Area (+ Special RMA 26) | 233 (+26) | UT 150, ID 14, WY 26, OR 14, WA 11, NV 5 |
| State Recreation Area | 115 | ID 31, MS 22, IN 13, AR 9, WI 6 |
| State Park | 77 | VT 14, ID 5, NV 4, NY 3 |
| Wildlife Mgmt Area | 55 | MS 20 |
| State Forest | 41 | WA 13, MI 6, NY 4 |
| State Rec Site | 37 | WA 16, AK 10 |
| State Fishing Lake | 33 | MS 15, OK 5, AR 3 |
| State Conservation Area | 28 | FL 17 |
| Wetland Mgmt District | 22 | MN 7 |
| Federal (NRA 17, Nat'l Forest 14, NWR 12, NHP 11, Monument 10, Nat'l Park 8) | ~72 | AL, NC, MT, OK, scattered |
| State Harbor | 13 | MI 13 |
Top states: UT 194, ID 63, MS 63, WA 55, WY 36, MI 35, OR 30, AR 25, AL 23, CA 22.

**Key point:** the BLM layer (`BLM_Natl_Recreation/MapServer/9`, `BLM_Natl_Recs_poly`) is ALREADY read (us-key/layers.json). So UT's 150 BLM RMAs are mostly name mismatch or areas not in that layer, not a missing layer. Do not add a new BLM layer first; run the name-match sample (see row 1 below).

## 2. Sources we already use (A)
state-gis.json: 58 areas; kinds park 41, land 37, wild 35, preserve 19, forest 8. **No state-gis entry at all for:** none empty, but these have NO park layer (land/wild only): ID, IN, NJ(land,preserve), ME, MD, CT, NH, NC(preserve,wild), VT(preserve), IL, DE. Federal: NPS tracts + legal boundary, FWS approved boundary + interest, BLM NLCS/recreation/WHB, Forest Service basic ownership, PAD-US (last), plus OSM (labelled unofficial).

## 3. Places we have NOT looked at (new official layers)
| # | Place type | Agency | Link | Grade | Why it matters |
|---|---|---|---|---|---|
| 1 | Name-match test, UT BLM RMAs | BLM | layer already read | A | do first: 30 UT names vs layer 9 |
| 2 | Bureau of Reclamation lands | BOR | https://services.arcgis.com/4OV0eRKiLAYkbH2J/ArcGIS/rest/services/Reclamation_Boundary/FeatureServer | B | recreation areas on western reservoirs (UT, WY, MT, CO, NV, CA, WA, ID) |
| 3 | Corps lakes (project lands) | USACE | https://services7.arcgis.com/n1YM8pTrFmm7L4hs/arcgis/rest/services/usace_rez (already used for closures) | A (name) / B | closures service already known; look for its matching land layer; HIFLD copy `usace_owned_and_operated_reservoirs` (maps.nccs.nasa.gov hifld_open/water_supply/MapServer/10) is a lake POINT/poly list only |
| 4 | Forest Service recreation | USFS | https://apps.fs.usda.gov/ArcX/rest/services/EDW/EDW_RecreationOpportunities_01/MapServer | B | "Recreation Site" types (AK 7, OK 4, WY 2, MT 2) are points; pin-only is correct unless the area is drawn |
| 5 | NOAA marine sanctuaries | NOAA ONMS | InPort 40112 / 37245 (fisheries.noaa.gov/inport/item/40112); Thunder Bay and others on sanctuaries.noaa.gov/library/imast/ | B | the few 'Marine Protected Area' / sanctuary parks (MN 2, FL, CA, HI, MI) |
| 6 | Estuarine Research Reserves | NOAA NERR | FL copy: https://ags.dep.state.fl.us/arcgis/rest/services/OpenData/AQUATIC_PRESERVES/MapServer/2 ; national set via NOAA OCM | B | coastal reserves are a POTA type some states list |
| 7 | National Heritage Areas | NPS | NPS Land Resources service (below) may not hold NHA; ask NPS open data hub (public-nps.opendata.arcgis.com) | C | 'National Heritage Area' appears in the type list |
| 8 | State fish hatcheries, fishing lakes | State wildlife agencies | via each state's wildlife GIS (OK, MS, AR, KS list 'State Fishing Lake') | C | 33 missing fishing lakes; these are small, many only a point |
| 9 | State harbors (MI 13) | Michigan DNR | Michigan Geographic Framework parks layer (already read, harbors not in it) | C | likely pin-only by nature |
| 10 | City/county/regional parks | cities, counties | no single source | C | Brandon ruled every POTA park in scope, but only a SURE official match goes on; keep pin-only until a county GIS is probed |
| 11 | DOE, military lands with public access | DOE, DoD | HIFLD / PAD-US only | C | few parks; PAD-US last |
| 12 | State fee lands MS WMA, MS rec areas | MS Dept of Wildlife (MDWFP), MS DEQ/MARIS | maris.state.ms.us (MS open-data portal) | C | MS has 63 missing, no park layer in state-gis; look in the open-data portal first (RESEARCH ORDER) |

## 4. MAJOR-RIVER OFFICIAL LAYERS (what to snag)
| # | Layer | Agency | Link | Grade | Use |
|---|---|---|---|---|---|
| R1 | National Wild and Scenic River Lines / Segments (all agencies, one layer) | Interagency (rivers.gov) | https://catalog.data.gov/dataset/national-wild-and-scenic-river-segments-feature-layer and ...-lines-feature-layer | B | designated river segments, line only |
| R2 | Wild & Scenic Rivers, Forest Service copy | USFS EDW | https://apps.fs.usda.gov/ArcX/rest/services/EDW/EDW_WildScenicRiverSegments_01/MapServer | B | same, easy to query |
| R3 | Wild & Scenic active study rivers | USFS EDW | .../EDW_WildScenicRiverActiveStudyRivers_01/MapServer/0 and /1 | B | not designated yet; keep out of "river = park" |
| R4 | Wild & Scenic legal status / eligible+suitable | catalog.data.gov | "National Wild and Scenic Rivers: Legal Status (Feature Layer)" | B | tells designated vs study |
| R5 | Nationwide Rivers Inventory (NRI) | NPS | https://services1.arcgis.com/fBc8EJBxQRMcHlei/ArcGIS/rest/services/Nationwide_Rivers_Inventory_Official/FeatureServer/0 | B | candidate rivers, lines; same NPS account as our tract layer |
| R6 | NPS Land Resources boundary + tracts (rivers inside parks) | NPS | https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/NPS_Land_Resources_Division_Boundary_and_Tract_Data_Service/FeatureServer/1 and /2 | A (used) | already the right owner source for NPS river corridors |
| R7 | NHDPlus HR + WBD (river/lake polygons, watershed lines) | USGS | https://hydro.nationalmap.gov/arcgis/rest/services/NHDPlus_HR/MapServer ; .../wbd/MapServer | B | water polygons for the water-only rule; USGS is already the water backup |
| R8 | State scenic/wild rivers | states | WI: geo.btaa.org record 121C3372-FD56-4D43-94C9-B5AEC781B5DA (Wild and Scenic Rivers WI 2019); VA: dcr.virginia.gov scenic rivers list (PDF, not GIS); TN: Tennessee GIS Water Data (data.amerigeoss.org/dataset/tennessee-gis-water-data); KY: Wild Rivers layer Brandon already found; IN: gisdata.in.gov NPS_River_Inventory_2023 FeatureServer | B/C | one per state; others (MI Natural Rivers, PA scenic, MO, AR ERW) not found |
| R9 | National Water Trails (NPS) | NPS | not found as a layer | C | skip until a source appears |

**Important limit (rule 8, still true):** a river layer is a LINE or a water polygon. A river counts inside a park only where the agency's OWN boundary says so; otherwise the pair is WATER ONLY (boat spot), never dropped. So rivers help the water map, they do not make a park outline.

## 5. BOT LOOK-UP rows
| Who | Row |
|---|---|
| chat 9 | Open each R1 R2 R5 R7 URL, print layer ids, fields, feature count, and run one point query at the Green River (KY, MACA) and the Ohio River at Louisville; report which gives a river line/polygon inside the NPS and FWS boundaries |
| chat 9 | Open BOR Reclamation_Boundary (row 2) and print fields; query 5 known BOR reservoirs (Flaming Gorge, Lake Powell, Lake Mead, Fort Peck, Lake Havasu) |
| chat 9 | For MS: open maris.state.ms.us data list and the MDWFP page; print any WMA/state-park polygon layer |
| chat 2 | Name-match test: 30 of the 150 UT BLM RMAs vs BLM_Natl_Recreation/MapServer/9 and BLM_Natl_Recs_poly (layer already read) |
| chat 2 | NOAA sanctuaries + NERR (rows 5, 6): fetch FGBNMS_py FeatureServer and the FL NERR layer; match the sanctuary-type POTA names |

## 6. Short answer for Brandon
918 US parks lack an outline; 60% sit in BLM areas (mostly Utah), state rec areas (Idaho, Mississippi, Indiana) and wildlife areas (Mississippi). The BLM layer is already read, so Utah is mostly a name-match job, not a missing layer. New sources worth a probe: Bureau of Reclamation, NOAA sanctuaries/reserves, Mississippi's open-data portal. Official river layers exist (Wild & Scenic, Nationwide Rivers Inventory, USGS NHD), but they are lines/water, so they feed the water map, not new park outlines.

Sources: [W&S segments](https://catalog.data.gov/dataset/national-wild-and-scenic-river-segments-feature-layer), [USFS W&S](https://apps.fs.usda.gov/ArcX/rest/services/EDW/EDW_WildScenicRiverSegments_01/MapServer), [NRI](https://services1.arcgis.com/fBc8EJBxQRMcHlei/ArcGIS/rest/services/Nationwide_Rivers_Inventory_Official/FeatureServer), [NHDPlus HR](https://hydro.nationalmap.gov/arcgis/rest/services/NHDPlus_HR/MapServer), [BOR](https://services.arcgis.com/4OV0eRKiLAYkbH2J/ArcGIS/rest/services/Reclamation_Boundary/FeatureServer), [NOAA sanctuaries](https://www.fisheries.noaa.gov/inport/item/40112), [BLM recreation](https://gis.blm.gov/arcgis/rest/services/recreation/BLM_Natl_Recreation/MapServer).
