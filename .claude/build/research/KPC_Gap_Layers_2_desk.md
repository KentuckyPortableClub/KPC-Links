# GAP LAYERS, ROUND 2 (Research desk, chat 8, Mon Oct 26 ~10:30 PM)

Rules kept: official sources, free, no key/login/token, no city park portals, no edits to data or pages. Grades: **A** = service page opened and layers/fields seen; **B** = service exists, layers or fields not seen; **C** = named from a search title only. Nothing here was test-queried (this session cannot). Chat 2's lead tester (`kpc_outline_lead_test.py`) and explorer (`kpc_parking_explorer.py`) do that.

## The big finding first
Most of the layers that should cover these gaps are **already read** (`data/state-gis.json`, `data/us-key/layers.json`, `data/ca-key/layers.json`, `data/outline-leads/tested.json`). So most remaining gaps are **name mismatches or parks the layer does not hold**, not missing layers. Only the finds marked NEW below are not in the repo. Check `parks_it_would_give` in `tested.json` for the layers marked READ before adding anything.

No-outline counts used (area-type parks only, from the answer keys): IN 19, WI 18, MN 17, NC 17 | NS 49, MB 35, AB 21, SK 7. Other states with 10 or more: MS 61, MI 54, UT 48, WA 29, ID 25, AR 25, MD 23, OR 23, WY 22, OK 20, NY 16, VT 16, TN 16, FL 16, NV 15, ND 14, AK 14, CA 14, AL 14, MT 12, IL 12, GA 11, MA 10, NE 10. (MS, MI, UT, WA, ID, AR, MD, OR, WY, OK, PE, NT, YT, QC, ON, NB, BC were round 1 or other rounds.)

## PART 1: OUTLINES (top 10 by likely parks covered)
| # | State/province | Agency | Link | Grade | Status | Would cover (est.) | Name match |
|---|---|---|---|---|---|---|---|
| 1 | CANADA (all provinces) | Environment and Climate Change Canada, CPCAD | https://services6.arcgis.com/qbvcda5wBEAxsCzs/arcgis/rest/services/Protected_Conserved_Area/FeatureServer | A (layer 0 "CPCAD", fields not shown) | **NEW**, not in repo. Download dated Oct 23 2023 (may be older than the provincial layers) | NS provincial parks, AB natural areas/PRAs, MB and SK parks, NWAs, bird sanctuaries: up to ~60 of the 112 NS/AB/MB/SK gaps | NOT SURE (field names unseen) |
| 2 | IN | Indiana DNR | https://gisdata.in.gov/server/rest/services/Hosted/ManagedLandsAll_DNR_INHD_IN_SP/FeatureServer/0 | A (polygon, `unitname`, manager, owner, acres, dedicated) | In `state-gis-found.json`, **not in the answer-key layers**. Sibling `ManagedLands_DNR_Open` is read. "All" holds nature preserves and non-open land the "Open" one leaves out. Page says it is "by no means complete" | 10 to 15 of 19 (state nature preserves, SRAs, fish and wildlife areas) | Likely: IN names end "State Nature Preserve"; `unitname` unseen in values |
| 3 | NC | NC Natural Heritage Program | https://services3.arcgis.com/YgrExeJfxG5F4At7/ArcGIS/rest/services/Managed_Areas_All/FeatureServer/0 | A (polygon, `MA_NAME`, CATEGORY, OWNER, GAP_STATUS) | In `state-gis-found.json`; the `ncnhde.natureserve.org ... Managed_Areas/MapServer/0` copy is READ. Probably the same data: ask chat 2 why the 8+ NC nature preserves did not match (name wording "State Nature Preserve" vs "Dedicated Nature Preserve") before treating as new | 8 to 10 of 17 | Name wording is the likely problem |
| 4 | WI | Wisconsin DNR | https://dnrmaps.wi.gov/arcgis/rest/services/LF_DML/LF_DNR_MGD_PROPERTY_WTM_Ext/MapServer | B (service text only; no name fields shown, layers list empty) | **NEW.** "DNR Managed Lands and Project Boundaries", dissolved by access code, so it may carry **no names** | up to 10 of 18 (state wildlife and recreation areas) if names exist | NOT SURE. Risky: dissolved polygons |
| 5 | WI | Wisconsin DNR (State Natural Areas) | https://dnrmaps.wi.gov/arcgis/rest/services/LF_DML/NHC_SNA_WTM_Ext/MapServer | C | NEW, name only from a search title | 0 to 3 | NOT SURE |
| 6 | MN + WI | US Fish and Wildlife Service, approved acquisition boundaries | https://services.arcgis.com/QVENGdaPbd4LUkLV/ArcGIS/rest/services/FWSApproved_Authoritative/FeatureServer/0 | A (polygon, `CMPXNAME`, `LABELNAME`, `RSL_TYPE`) | **READ** (in `us-key/layers.json`). The 7 MN and 2 WI "Wetland Management District" parks and the MN "Aquatic Reserve" are still missing, so check the wording: layer names look like "Agassiz NWR" style codes, WMDs may be under "Complex" names | 9 (MN 7 WMDs, WI 2) | Probably not: WMD names differ. Needs a name alias |
| 7 | NC | National Park Service (Blue Ridge Parkway: Moses H. Cone, Julian Price, Doughton) | https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/NPS_Land_Resources_Division_Boundary_and_Tract_Data_Service/FeatureServer (layer 2 "NPS Boundary") | A (layers 0 to 2 seen; fields unseen) | **READ**. These are parts of one parkway unit, so the whole-parkway polygon is not the same as the park | 3 | Poor: unit is "Blue Ridge Parkway" |
| 8 | MB | Manitoba Sustainable Development (Parks) | https://services.arcgis.com/mMUesHYPkXjaFGfS/ArcGIS/rest/services/Manitoba_Parks/FeatureServer/0 | A (polygon, `NAME_E`, `TYPE_E`, 92 parks + 1 reserve, current to June 2017) | **READ**. 2017 data: newer parks and "Recreation Park" wayside sites are missing. Gaps like "Whittier Recreation Park", "Ernie O' Dowda Recreation Park", "Primrose Wayside" are probably not in it | 0 new | Names match (Manitoba "X Provincial Park") |
| 9 | MB | Manitoba (Wildlife Management Areas) | https://open.canada.ca/data/en/dataset/40c5bcb8-ff4e-2a3b-d0ef-16a0d471902f ("Manitoba Wildlife Lands MAP-2024") | C (data portal record only; a map, maybe a PDF) | NEW. The 7+ MB WMD/WMA gaps (Cape Tatnam, Ellice-Archie, Ethelbert, Gardenton-Pansy...) need a polygon layer | up to 8 | NOT SURE |
| 10 | SK | Saskatchewan Ministry of Parks, Culture and Sport | https://gis.saskatchewan.ca/arcgis/rest/services/ParksAsLegislated/FeatureServer/5 (layers 0 to 5 seen: "Provincial Park as Legislated", "Hunting Allowed Parks as Legislated") | A (polygon, `PARKNM`, `PARKTYPE`) | **READ**. The 7 SK gaps are regional parks, a park reserve, a resource management area and National Wildlife Areas, which this layer does not hold. National Wildlife Areas: only a third-party (Ducks Unlimited) copy of Environment Canada's 2014 layer surfaced (https://maps.ducks.ca/arcgis/rest/services/Public/NWA/MapServer). **Not official host, do not use**; CPCAD (#1) covers NWAs | 0 to 3 | n/a |

**Nova Scotia (49 gaps, the largest in this round):** NovaRoc layers 29 and 52 and the Parks and Protected Areas layer are READ, but 14+ gaps are plain "Provincial Park" names (Lawrencetown Beach, Scots Bay, Sherbrooke, Rainbow Haven...). NS publishes a boundary PDF per park (e.g. https://novascotia.ca/natr/parks/management/carters-beach-boundary-map.pdf, grade C: PDF only, not usable as polygons). CPCAD (#1) is the best lead; NOT SURE it lists NS provincial parks.

**Alberta (21 gaps):** `parks_protected_areas_alberta` is READ (https://geospatial.alberta.ca/titan/rest/services/boundary/parks_protected_areas_alberta/FeatureServer, A: one layer "Protected Area Designations", "replaces nine earlier datasets", written legal descriptions win). Gaps are PRAs and Natural Areas the layer should hold, so this is a **name-wording problem** ("Big Elbow Provincial Recreation Area" vs the layer's short names). Also in Alberta: https://geospatial.alberta.ca/arcgis/rest/services/Hosted/CPML_2025_26/MapServer/6 ("Protected Area Designation", B, a newer 2025/26 hosted copy: worth a test).

**States with no new find:** VT, TN, FL, NY, CA, AL, GA, MA, NE (10+ gaps each). The desk found no new official layer for them beyond what `state-gis.json` already lists. TVA lands (TN, AL): only TVA's planning-zone pages surfaced, no polygon service (C, https://www.tva.com/environment/recreation/small-wild-areas).

**Order for chat 2:** (1) test CPCAD fields against the NS/AB/MB/SK gap names, (2) test IN ManagedLandsAll "All" against the 19 IN names, (3) find out why NC nature preserves did not match `Managed_Areas`, (4) test the AB 2025/26 hosted copy, (5) WI Managed Property only if names exist.

## PART 2: PARKING AND ACCESS POINTS
**Assumption (flag for HQ to correct):** the repo has no per-state activity count, so the top 10 states outside Kentucky are taken as **FL, PA, NY, NC, VA, GA, OH, TX, CA, MI**.

What is read (`data/access-layers.json`, 246 layers): every state in that list already has state-agency points (FL 9, PA 7, NY 5, NC 2, VA 8, GA 4, OH 4, TX 4, CA 4, MI 5). **No federal layer is read at all**: Forest Service, National Park Service, Fish and Wildlife refuges, BLM, Army Corps. That is the real gap, and it helps every one of the 10 states at once.

| # | Scope | Agency | Link | Grade | Holds | Notes |
|---|---|---|---|---|---|---|
| 1 | All states | USDA Forest Service | https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_RecreationOpportunities_01/MapServer/0 | A (one point layer, "Recreation Opportunities", RECAREAID, updated nightly, visible at 1:400,000) | Forest Service recreation sites and areas: campgrounds, picnic and day-use, trailheads, boat launches | **NEW.** Official, free. Biggest single gain: NC (Pisgah, Nantahala), GA, VA, PA (Allegheny), MI, NY, CA, TX, OH. Fields not shown to the desk: test `RECAREANAME`, `MARKERACTIVITY`, `OPEN_STATUS` |
| 2 | All states | USDA Forest Service (activities table) | https://apps.fs.usda.gov/ArcX/rest/services/EDW/EDW_RecreationAreaActivities_01/MapServer | B (service seen in search, not opened) | Activities per recreation area (hiking, boating, camping) | NEW. Pairs with #1 to tell trailhead from campground |
| 3 | NC | NC Wildlife Resources Commission | already READ (game land parking, boating access areas) | A (in repo) | | Nothing new. NC State Parks has **no** official point layer found (see below) |
| 4 | NC | NC OneMap, "NC1Map_Recreation" | https://services.nconemap.gov/secure/rest/services/NC1Map_Recreation/FeatureServer | A (but only 2 layers: Paddle Trails points and arcs, Coastal Plain) | Paddle trail access points | NEW but small; the address has "/secure/" in it, so token need is NOT SURE |
| 5 | WI | Wisconsin DNR | https://dnrmaps.wi.gov/arcgis/rest/services/LF_DML/LF_DNR_BOAT_BoatAccess_WTM_Ext/MapServer | B | Boat access | WI is outside the assumed top 10; same data as `PR_Boat_Access_Shore_Fishing` (READ), so skip |
| 6 | TX | Texas Parks and Wildlife | https://tpwd.texas.gov/arcgis/rest/services/Parks/TexasStateParksTrails/MapServer/0 | A (layer 0 "State Parks Trails", vetted by park staff) | Trail lines for state parks (not points) | NEW for trails, not access points. Belongs with the trails file, not the access file |
| 7 | GA | Georgia DNR | https://services1.arcgis.com/aT1T0pU1ZdpuDk1t/ArcGIS/rest/services/StateParks/FeatureServer | A (one layer "State Parks", parcel boundaries at 1:24,000) | State park parcel polygons | In `state-gis-found.json`. A boundary layer, **not** access points. Belongs to Part 1 for GA state parks |
| 8 | All states | National Park Service | NOT SURE | none | NPS parking and trailheads | The desk found no official NPS point layer for parking. The "NPS Boundary Centroids" layer (https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/NPS_Land_Resources_Division_Boundary_and_Tract_Data_Service/FeatureServer/0) gives one point per unit, which is a unit centre, not an entrance. Do not use as access |
| 9 | All states | Fish and Wildlife Service refuges | NOT SURE | none | Refuge parking and trails | Search surfaced only the approved-boundary polygons (see Part 1 #6) and a regional SE copy (https://services.arcgis.com/v01gqwM5QqNysAAi/ArcGIS/rest/services/SE_NWR_approved/FeatureServer, B) |
| 10 | All states | Army Corps of Engineers | NOT SURE | none | Lake recreation areas, ramps | Search surfaced only per-lake PDF maps (e.g. https://www.swf-wc.usace.army.mil/belton/images/BELTON_LAKE_OVERALL_RECREATION_MAP.pdf) and the Corps Lakes pages. No polygon or point service found |

Honest count: **only #1 and #2 are strong new finds**; #4 and #6 are small. The desk could not find 10 verified layers. Items 8 to 10 are listed so chat 2 does not search them again.

## PART 3: CAMPGROUNDS
What is read: `data/campfed/` = Recreation.gov (RIDB) federal campgrounds, which already include **Forest Service, NPS, Corps and BLM campgrounds that take reservations or are listed in RIDB**. State camp files exist for AK AZ CA CO FL HI IA IN MA MI MN MT NE NH NY OH OK OR PA RI SD TN TX UT VA VT WA WV WY. **No file for NC, GA, WI** (and others outside the assumed 10).

| # | Scope | Agency | Link | Grade | Holds | Notes |
|---|---|---|---|---|---|---|
| 1 | All states | USDA Forest Service Recreation Opportunities (same as Part 2 #1) | https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_RecreationOpportunities_01/MapServer/0 | A | Forest Service campgrounds **including first-come ones RIDB may miss** | NEW. Filter to camping types |
| 2 | WI | Wisconsin DNR | https://dnrmaps.wi.gov/arcgis/rest/services/LF_DML/LF_DNR_MGD_Recreational_Opp_WTM_Ext/MapServer | B ("recreational lands and facilities... DNR and non-DNR", layer list empty) | State park and forest campgrounds, boat access | NEW. WI has 0 camp layers read |
| 3 | WI | Wisconsin DNR (AGOL copy) | https://dnrmaps.wi.gov/arcgis/rest/services/LF_DML/AGOL_DNR_REC_OPPS_WTM_Ext/MapServer | B | Same data, "Rec Opps" | Test with #2; one of the two will list layers |
| 4 | TX | Texas Parks and Wildlife | https://services1.arcgis.com/1mtXwieMId59thmg/ArcGIS/rest/services/Texas_State_Parks_Public_Areas/FeatureServer/2 | A (layer 2 "Campground Area"; layers 0 to 5 seen) | State park campground areas | **READ** (in `campstate/layers.json`). No gap |
| 5 | TX | Texas Water Development Board | https://gis1.twdb.texas.gov/server/rest/services/WSC-FSCA-FM/Texas_Campgrounds/MapServer | B (layers not opened) | A statewide campground layer | NEW. Agency is a water board, so origin of the data is NOT SURE; check the source field before trusting |
| 6 | NC | NC State Parks | NOT SURE | none | | No official NC State Parks camp or facility layer was found. Chatham and Wake county layers surfaced (county, skipped) |
| 7 | GA | Georgia DNR (State Parks) | NOT SURE | none | | The one GA state-parks service found holds parcel polygons only |
| 8 | GA, NC, VA, PA, others | Corps / TVA | NOT SURE | none | | See Part 2 #10 |
| 9 | All | NPS | NOT SURE | none | | NPS campgrounds come through RIDB already |
| 10 | NC, GA | National Forest campgrounds | covered by #1 | | | Pisgah, Nantahala, Chattahoochee all inside #1 |

Honest count: **#1 is the strong find**, #2 to #3 (WI) and #5 (TX) are leads. NC and GA state-park camps have no official open layer the desk could find.

## What was NOT checked
- Whether any service answers a query, how many records it holds, or the real field values (needs chat 2's tester).
- Per-state POTA activity (assumed list above).
- Counties and cities (skipped on purpose).

## Sources (all opened or surfaced by search this session)
- https://gisdata.in.gov/server/rest/services/Hosted/ManagedLandsAll_DNR_INHD_IN_SP/FeatureServer/0
- https://dnrmaps.wi.gov/arcgis/rest/services/LF_DML/LF_DNR_MGD_PROPERTY_WTM_Ext/MapServer
- https://services3.arcgis.com/YgrExeJfxG5F4At7/ArcGIS/rest/services/Managed_Areas_All/FeatureServer/0
- https://geospatial.alberta.ca/titan/rest/services/boundary/parks_protected_areas_alberta/FeatureServer
- https://gis.saskatchewan.ca/arcgis/rest/services/ParksAsLegislated/FeatureServer/5
- https://services.arcgis.com/mMUesHYPkXjaFGfS/ArcGIS/rest/services/Manitoba_Parks/FeatureServer/0
- https://services6.arcgis.com/qbvcda5wBEAxsCzs/arcgis/rest/services/Protected_Conserved_Area/FeatureServer
- https://services.arcgis.com/QVENGdaPbd4LUkLV/ArcGIS/rest/services/FWSApproved_Authoritative/FeatureServer/0
- https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/NPS_Land_Resources_Division_Boundary_and_Tract_Data_Service/FeatureServer
- https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_RecreationOpportunities_01/MapServer
- https://tpwd.texas.gov/arcgis/rest/services/Parks/TexasStateParksTrails/MapServer
- https://services1.arcgis.com/1mtXwieMId59thmg/ArcGIS/rest/services/Texas_State_Parks_Public_Areas/FeatureServer
- https://services1.arcgis.com/aT1T0pU1ZdpuDk1t/ArcGIS/rest/services/StateParks/FeatureServer
- https://services.nconemap.gov/secure/rest/services/NC1Map_Recreation/FeatureServer/layers?f=pjson
- https://dnrmaps.wi.gov/arcgis/rest/services/LF_DML/LF_DNR_MGD_Recreational_Opp_WTM_Ext/MapServer
- https://maps.ducks.ca/arcgis/rest/services/Public/NWA/MapServer
